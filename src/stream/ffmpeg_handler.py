"""
FFmpeg Stream Handler
Verarbeitet Video-Input über ffmpeg (SDI, HDMI, Webcam)
"""

import subprocess
import numpy as np
import platform
import re
from typing import Optional, Tuple
from pathlib import Path

from src.utils.logger import get_logger
from src import config
from src.stream.video_source import VideoSource


logger = get_logger(__name__)


def detect_device_by_name(device_name: str, system: str = None) -> Optional[str]:
    """
    Sucht ein ffmpeg-Device anhand des Namens und gibt den Index zurück
    
    Args:
        device_name: Name des zu suchenden Devices (z.B. "Cam Link 4K")
        system: OS-Name (Darwin, Linux, Windows). Wird automatisch erkannt falls None
        
    Returns:
        Device-Index als String (z.B. "0", "1") oder None wenn nicht gefunden
    """
    if system is None:
        system = platform.system()
    
    # Nur für macOS mit avfoundation
    if system != "Darwin":
        logger.warning(f"Automatische Device-Erkennung nur für macOS unterstützt")
        return None
    
    try:
        # ffmpeg Device-Liste abrufen
        cmd = ['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', '']
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=5
        )
        
        # Nach Device-Name suchen
        # Format: [AVFoundation indev @ 0x...] [0] Device Name
        pattern = rf'\[AVFoundation.*\] \[(\d+)\] {re.escape(device_name)}'
        match = re.search(pattern, result.stdout)
        
        if match:
            device_index = match.group(1)
            logger.info(f"✓ Device '{device_name}' gefunden bei Index [{device_index}]")
            return device_index
        else:
            logger.warning(f"Device '{device_name}' nicht gefunden in ffmpeg Device-Liste")
            return None
            
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout bei ffmpeg Device-Erkennung")
        return None
    except FileNotFoundError:
        logger.error(f"ffmpeg nicht gefunden. Bitte installieren: brew install ffmpeg")
        return None
    except Exception as e:
        logger.error(f"Fehler bei Device-Erkennung: {e}")
        return None


class FFmpegStreamHandler(VideoSource):
    """
    Verarbeitet Video-Streams über ffmpeg
    """
    
    def __init__(
        self,
        device: str = None,
        resolution: Tuple[int, int] = None,
        fps: int = None
    ):
        """
        Args:
            device: Device-Name (Blackmagic, Elgato, Webcam, etc.)
            resolution: (width, height)
            fps: Ziel-FPS
        """
        super().__init__()
        
        self.device = device or config.FFMPEG_INPUT_DEVICE
        self.resolution = resolution or config.RESOLUTION
        self.fps = fps or config.FPS_TARGET
        
        self.process = None
        self.frame_size = self.resolution[0] * self.resolution[1] * 3  # BGR
        self.system = platform.system()
        
        logger.info(f"FFmpeg Handler initialisiert: {self.device}")
        logger.info(f"Resolution: {self.resolution[0]}x{self.resolution[1]}")
        logger.info(f"FPS: {self.fps}")
        logger.info(f"System: {self.system}")
    
    def _build_ffmpeg_command(self) -> list:
        """
        Baut das ffmpeg-Kommando basierend auf Device und System
        
        Returns:
            Liste mit Kommando-Argumenten
        """
        # Basis-Kommando
        cmd = ['ffmpeg']
        
        # Input-Format basierend auf System
        if self.system == "Darwin":  # macOS
            input_format = "avfoundation"
        elif self.system == "Linux":
            input_format = "v4l2"
        else:  # Windows
            input_format = "dshow"
        
        # Device-Name aus Konfiguration
        device_name = config.FFMPEG_DEVICE_NAMES.get(
            self.device,
            self.device
        )
        
        # Automatische Device-Erkennung für Elgato (macOS)
        if self.device == "Elgato" and self.system == "Darwin":
            detected = detect_device_by_name("Cam Link 4K", self.system)
            if detected is not None:
                device_name = detected
                logger.info(f"Verwende automatisch erkannten Device-Index: {device_name}")
            else:
                logger.warning(f"Automatische Erkennung fehlgeschlagen, verwende Fallback: {device_name}")
        
        
        # Input-Parameter (WICHTIG: framerate und video_size VOR -i)
        if self.system == "Darwin":
            # macOS: avfoundation benötigt explizite Parameter
            # Input mit 50 FPS, Output mit 25 FPS (ffmpeg übernimmt Frame-Skipping)
            cmd.extend([
                '-f', input_format,
                '-pixel_format', 'uyvy422',  # Natives Cam Link Format
                '-framerate', str(self.fps),  # 50 FPS Input
                '-video_size', f'{self.resolution[0]}x{self.resolution[1]}',
                '-i', device_name,
                '-r', '25'  # Output: 25 FPS (ffmpeg überspringt jeden 2. Frame)
            ])
        elif self.system == "Linux":
            cmd.extend([
                '-f', input_format,
                '-framerate', str(self.fps),
                '-video_size', f'{self.resolution[0]}x{self.resolution[1]}',
                '-i', f'/dev/video{device_name}'
            ])
        else:  # Windows
            cmd.extend([
                '-f', input_format,
                '-framerate', str(self.fps),
                '-video_size', f'{self.resolution[0]}x{self.resolution[1]}',
                '-i', f'video={device_name}'
            ])
        
        # Output-Parameter
        cmd.extend([
            '-pix_fmt', 'bgr24',  # Pixel-Format (BGR für OpenCV)
            '-f', 'rawvideo',  # Output-Format
            '-'  # Output zu stdout
        ])
        
        return cmd
    
    def open(self) -> bool:
        """
        Startet den ffmpeg-Prozess
        
        Returns:
            True wenn erfolgreich
        """
        try:
            logger.info(f"Starte ffmpeg-Prozess für {self.device}...")
            
            # Kommando bauen
            cmd = self._build_ffmpeg_command()
            logger.info(f"FFmpeg Kommando: {' '.join(cmd)}")
            
            # Prozess starten (stderr nach DEVNULL um Blocking zu vermeiden)
            # bufsize=0 für unbuffered I/O (wichtig für Echtzeit-Streaming)
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,  # Vermeide stderr-Blocking
                bufsize=0  # Unbuffered I/O für kontinuierliches Streaming
            )
            
            # Kurz warten und prüfen ob Prozess läuft
            import time
            time.sleep(1.0)  # Länger warten für Device-Initialisierung
            
            if self.process.poll() is not None:
                # Prozess wurde beendet
                logger.error(f"FFmpeg-Prozess wurde beendet (Exit Code: {self.process.returncode})")
                return False
            
            logger.info("✓ FFmpeg-Prozess gestartet")
            self.is_opened = True
            return True
            
        except FileNotFoundError:
            logger.error("ffmpeg wurde nicht gefunden. Bitte installieren: brew install ffmpeg")
            return False
        except Exception as e:
            logger.error(f"Fehler beim Öffnen der Video-Quelle: {e}")
            return False
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Liest einen Frame vom ffmpeg-Stream
        
        Returns:
            (success, frame)
        """
        if not self.is_opened or self.process is None:
            return False, None
        
        try:
            # Prüfe ob Prozess noch läuft
            if self.process.poll() is not None:
                logger.error("FFmpeg-Prozess wurde beendet")
                self.is_opened = False
                return False, None
            
            # Kompletten Frame lesen
            raw_frame = self._read_full_frame()
            if raw_frame is None:
                return False, None
            
            # Bytes zu NumPy-Array konvertieren
            frame = np.frombuffer(raw_frame, dtype=np.uint8)
            frame = frame.reshape((self.resolution[1], self.resolution[0], 3))
            
            self.frame_count += 1
            return True, frame
            
        except Exception as e:
            logger.error(f"Fehler beim Frame-Lesen: {e}")
            return False, None
    
    def _read_full_frame(self) -> Optional[bytes]:
        """
        Liest einen kompletten Frame in einer Schleife
        Notwendig weil read() nicht immer alle Bytes auf einmal liefert
        
        Returns:
            Frame als Bytes oder None bei Fehler
        """
        raw_frame = b''
        bytes_remaining = self.frame_size
        
        while bytes_remaining > 0:
            chunk = self.process.stdout.read(bytes_remaining)
            
            if not chunk:
                # Keine Daten mehr verfügbar
                if len(raw_frame) > 0:
                    logger.warning(f"Unvollständiger Frame: {len(raw_frame)} von {self.frame_size} Bytes")
                return None
            
            raw_frame += chunk
            bytes_remaining -= len(chunk)
        
        return raw_frame
    
    def release(self):
        """
        Beendet den ffmpeg-Prozess
        """
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("FFmpeg-Prozess reagiert nicht, erzwinge Beendigung...")
                self.process.kill()
                self.process.wait()
            finally:
                self.process = None
        
        self.is_opened = False
        logger.info("FFmpeg Handler geschlossen")
    
    def get_resolution(self) -> Tuple[int, int]:
        """Returns: (width, height)"""
        return self.resolution
    
    def get_fps(self) -> float:
        """Returns: FPS"""
        return float(self.fps)


if __name__ == "__main__":
    # Test
    import time
    
    logger.info("Testing FFmpeg Handler...")
    logger.info("-" * 60)
    logger.info("⚠️  Hinweis: Dieser Test benötigt ein aktives Video-Device")
    logger.info("")
    
    handler = FFmpegStreamHandler()
    
    if handler.open():
        logger.info("Lese 10 Frames...")
        
        for i in range(10):
            success, frame = handler.read()
            if success:
                logger.info(f"Frame {i+1}: {frame.shape}")
            else:
                logger.warning(f"Frame {i+1}: Fehler beim Lesen")
            time.sleep(0.1)
        
        handler.release()
        logger.info("✓ Test erfolgreich")
    else:
        logger.error("✗ FFmpeg konnte nicht gestartet werden")
        logger.info("Tipps:")
        logger.info("  - ffmpeg installiert? brew install ffmpeg")
        logger.info("  - Device in config.py korrekt?")
        logger.info("  - Device-Liste: ffmpeg -f avfoundation -list_devices true -i \"\"")
    
    logger.info("-" * 60)


if __name__ == "__main__":
    # Test
    logger.info("Testing FFmpeg Handler...")
    
    handler = FFmpegStreamHandler()
    
    with handler:
        success, frame = handler.read()
        if success:
            logger.info(f"Frame gelesen: {frame.shape}")
        else:
            logger.warning("Kein Frame gelesen (noch nicht implementiert)")
    
    logger.info("Test abgeschlossen")
