"""
GStreamer Stream Handler
Verarbeitet Video-Input über GStreamer (DeckLink, V4L2, etc.)
Native Integration für Blackmagic DeckLink und V4L2-Devices

Features:
- Native DeckLink-Support via decklinkvideosrc
- V4L2-Support für Linux (Elgato, USB-Capture)
- AVFoundation für macOS (Elgato, USB-Capture)
- Hardware-beschleunigte Verarbeitung
- Zero-copy Buffer-Handling
- Granulare Latenz-Kontrolle
"""

import numpy as np
import platform
import time
from typing import Optional, Tuple

from src.utils.logger import get_logger
from src import config
from src.stream.video_source import VideoSource


logger = get_logger(__name__)

# GStreamer Import
try:
    import gi
    gi.require_version('Gst', '1.0')
    gi.require_version('GstApp', '1.0')
    from gi.repository import Gst, GstApp
    
    # GStreamer initialisieren
    Gst.init(None)
    GST_AVAILABLE = True
    logger.info("✓ GStreamer erfolgreich geladen")
except ImportError as e:
    GST_AVAILABLE = False
    logger.error(f"GStreamer nicht verfügbar: {e}")
    logger.error("Installation: macOS: brew install gstreamer gst-python gst-plugins-base gst-plugins-good gst-plugins-bad")
    logger.error("Installation: Linux: apt-get install python3-gi gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad")


class GStreamerHandler(VideoSource):
    """
    Verarbeitet Video-Streams über GStreamer
    
    Unterstützte Quellen:
    - DeckLink: Blackmagic Capture-Cards (decklinkvideosrc)
    - V4L2: Linux Video4Linux2 Devices (v4l2src)
    - AVFoundation: macOS Capture-Devices (avfvideosrc)
    """
    
    def __init__(
        self,
        device: str = None,
        resolution: Tuple[int, int] = None,
        fps: int = None,
        device_number: int = 0,
        connection: str = "sdi"  # sdi, hdmi, optical-sdi, component, composite, s-video
    ):
        """
        Args:
            device: Device-Typ (Blackmagic, Elgato, Webcam)
            resolution: (width, height)
            fps: Ziel-FPS
            device_number: Device-Nummer für decklinkvideosrc oder v4l2src
            connection: DeckLink-Verbindungstyp (sdi, hdmi, etc.)
        """
        super().__init__()
        
        if not GST_AVAILABLE:
            raise RuntimeError("GStreamer ist nicht verfügbar. Bitte installieren.")
        
        self.device = device or config.GSTREAMER_INPUT_DEVICE
        self.resolution = resolution or config.RESOLUTION
        self.fps = fps or config.FPS_TARGET
        self.device_number = device_number
        self.connection = connection
        self.system = platform.system()
        
        self.pipeline = None
        self.appsink = None
        self.bus = None
        
        # Frame-Buffer
        self.current_frame = None
        self.frame_ready = False
        
        logger.info(f"GStreamer Handler initialisiert: {self.device}")
        logger.info(f"System: {self.system}")
        logger.info(f"Resolution: {self.resolution[0]}x{self.resolution[1]}")
        logger.info(f"FPS: {self.fps}")
        if self.device == "Blackmagic":
            logger.info(f"DeckLink Device: {self.device_number}, Connection: {self.connection}")
    
    def _build_pipeline_string(self) -> str:
        """
        Baut den GStreamer-Pipeline-String basierend auf Device und System
        
        Returns:
            Pipeline-String für gst-launch
        """
        width, height = self.resolution
        
        # DeckLink (Blackmagic) - funktioniert auf macOS und Linux
        if self.device == "Blackmagic":
            pipeline = (
                f"decklinkvideosrc device-number={self.device_number} "
                f"connection={self.connection} mode=1080p{self.fps} "
                f"! videoconvert "
                f"! video/x-raw,format=BGR,width={width},height={height},framerate={self.fps}/1 "
                f"! appsink name=sink max-buffers=2 drop=true emit-signals=true"
            )
        
        # Linux: V4L2 für USB-Capture (Elgato, etc.)
        elif self.system == "Linux":
            pipeline = (
                f"v4l2src device=/dev/video{self.device_number} "
                f"! videoconvert "
                f"! video/x-raw,format=BGR,width={width},height={height},framerate={self.fps}/1 "
                f"! appsink name=sink max-buffers=2 drop=true emit-signals=true"
            )
        
        # macOS: AVFoundation für USB-Capture (Elgato, etc.)
        elif self.system == "Darwin":
            # Automatische Device-Erkennung für Elgato
            device_id = self._detect_avfoundation_device()
            
            pipeline = (
                f"avfvideosrc device-index={device_id} "
                f"! video/x-raw,width={width},height={height},framerate={self.fps}/1 "
                f"! videoconvert "
                f"! video/x-raw,format=BGR "
                f"! appsink name=sink max-buffers=2 drop=true emit-signals=true"
            )
        
        else:
            raise RuntimeError(f"Nicht unterstütztes System: {self.system}")
        
        return pipeline
    
    def _detect_avfoundation_device(self) -> int:
        """
        Erkennt AVFoundation-Device-Index für Elgato/Cam Link
        
        Returns:
            Device-Index oder 0 als Fallback
        """
        if self.device != "Elgato":
            return self.device_number
        
        # Verwende gst-device-monitor für Device-Erkennung
        try:
            import subprocess
            result = subprocess.run(
                ['gst-device-monitor-1.0', 'Video'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Suche nach "Cam Link" im Output
            lines = result.stdout.split('\n')
            for i, line in enumerate(lines):
                if 'Cam Link' in line or 'Elgato' in line:
                    # Versuche Device-Index zu extrahieren
                    for j in range(max(0, i-5), min(len(lines), i+5)):
                        if 'device.index' in lines[j]:
                            try:
                                idx = int(lines[j].split('=')[1].strip())
                                logger.info(f"✓ Elgato gefunden bei Index {idx}")
                                return idx
                            except:
                                pass
            
            logger.warning(f"Elgato nicht automatisch erkannt, verwende Device {self.device_number}")
            return self.device_number
            
        except Exception as e:
            logger.debug(f"Device-Erkennung fehlgeschlagen: {e}")
            return self.device_number
    
    def open(self) -> bool:
        """
        Erstellt und startet die GStreamer-Pipeline
        
        Returns:
            True wenn erfolgreich
        """
        try:
            logger.info(f"Erstelle GStreamer-Pipeline für {self.device}...")
            
            # Pipeline-String bauen
            pipeline_str = self._build_pipeline_string()
            logger.info(f"Pipeline: {pipeline_str}")
            
            # Pipeline erstellen
            self.pipeline = Gst.parse_launch(pipeline_str)
            
            if not self.pipeline:
                logger.error("Pipeline konnte nicht erstellt werden")
                return False
            
            # AppSink-Element referenzieren
            self.appsink = self.pipeline.get_by_name('sink')
            
            if not self.appsink:
                logger.error("AppSink nicht gefunden in Pipeline")
                return False
            
            # AppSink konfigurieren
            self.appsink.set_property('emit-signals', True)
            self.appsink.set_property('max-buffers', 2)
            self.appsink.set_property('drop', True)
            
            # Callback für neue Samples
            self.appsink.connect('new-sample', self._on_new_sample)
            
            # Bus für Fehlermeldungen
            self.bus = self.pipeline.get_bus()
            self.bus.add_signal_watch()
            self.bus.connect('message::error', self._on_error)
            self.bus.connect('message::warning', self._on_warning)
            self.bus.connect('message::eos', self._on_eos)
            
            # Pipeline starten
            ret = self.pipeline.set_state(Gst.State.PLAYING)
            
            if ret == Gst.StateChangeReturn.FAILURE:
                logger.error("Pipeline konnte nicht gestartet werden")
                return False
            
            # Warten bis Pipeline läuft
            state_change = self.pipeline.get_state(timeout=5 * Gst.SECOND)
            if state_change[0] != Gst.StateChangeReturn.SUCCESS:
                logger.error(f"Pipeline-State-Change fehlgeschlagen: {state_change}")
                return False
            
            logger.info("✓ GStreamer-Pipeline gestartet")
            self.is_opened = True
            
            # Kurz warten für ersten Frame
            time.sleep(0.5)
            
            return True
            
        except Exception as e:
            logger.exception(f"Fehler beim Öffnen der GStreamer-Pipeline: {e}")
            return False
    
    def _on_new_sample(self, appsink):
        """
        Callback für neue Frames vom AppSink
        
        Args:
            appsink: GStreamer AppSink-Element
        
        Returns:
            Gst.FlowReturn.OK
        """
        sample = appsink.emit('pull-sample')
        
        if sample:
            buffer = sample.get_buffer()
            caps = sample.get_caps()
            
            # Caps-Struktur auslesen
            structure = caps.get_structure(0)
            width = structure.get_value('width')
            height = structure.get_value('height')
            
            # Buffer zu NumPy-Array konvertieren
            success, map_info = buffer.map(Gst.MapFlags.READ)
            
            if success:
                try:
                    # BGR-Frame erstellen
                    frame = np.ndarray(
                        shape=(height, width, 3),
                        dtype=np.uint8,
                        buffer=map_info.data
                    )
                    
                    # Frame speichern (Deep Copy für Thread-Safety)
                    self.current_frame = frame.copy()
                    self.frame_ready = True
                    self.frame_count += 1
                    
                finally:
                    buffer.unmap(map_info)
        
        return Gst.FlowReturn.OK
    
    def _on_error(self, bus, message):
        """Error-Handler für GStreamer-Bus"""
        err, debug = message.parse_error()
        logger.error(f"GStreamer Error: {err}, Debug: {debug}")
    
    def _on_warning(self, bus, message):
        """Warning-Handler für GStreamer-Bus"""
        warn, debug = message.parse_warning()
        logger.warning(f"GStreamer Warning: {warn}, Debug: {debug}")
    
    def _on_eos(self, bus, message):
        """End-of-Stream-Handler"""
        logger.info("GStreamer: End of Stream erreicht")
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Liest den aktuellen Frame
        
        Returns:
            (success, frame)
        """
        if not self.is_opened or not self.pipeline:
            return False, None
        
        # Prüfe Pipeline-State
        state = self.pipeline.get_state(timeout=0)
        if state[1] != Gst.State.PLAYING:
            logger.error(f"Pipeline nicht im PLAYING-State: {state[1]}")
            return False, None
        
        # Frame verfügbar?
        if self.frame_ready and self.current_frame is not None:
            return True, self.current_frame
        else:
            # Kurz warten auf Frame (für ersten Frame)
            max_wait = 0.1  # 100ms
            waited = 0
            while not self.frame_ready and waited < max_wait:
                time.sleep(0.01)
                waited += 0.01
            
            if self.frame_ready and self.current_frame is not None:
                return True, self.current_frame
            else:
                return False, None
    
    def release(self):
        """
        Stoppt die Pipeline und gibt Ressourcen frei
        """
        if self.pipeline:
            # Pipeline stoppen
            self.pipeline.set_state(Gst.State.NULL)
            
            # Warten bis gestoppt
            self.pipeline.get_state(timeout=2 * Gst.SECOND)
            
            # Referenzen freigeben
            if self.bus:
                self.bus.remove_signal_watch()
                self.bus = None
            
            self.appsink = None
            self.pipeline = None
        
        self.is_opened = False
        self.current_frame = None
        self.frame_ready = False
        
        logger.info("GStreamer Handler geschlossen")
    
    def get_resolution(self) -> Tuple[int, int]:
        """Returns: (width, height)"""
        return self.resolution
    
    def get_fps(self) -> float:
        """Returns: Frames pro Sekunde"""
        return float(self.fps)


# Utility-Funktionen für GStreamer-Info
def list_gstreamer_devices():
    """
    Listet verfügbare GStreamer-Video-Devices auf
    Nützlich für Debugging und Setup
    """
    if not GST_AVAILABLE:
        logger.error("GStreamer nicht verfügbar")
        return
    
    logger.info("Verfügbare GStreamer Video-Devices:")
    logger.info("=" * 60)
    
    import subprocess
    
    try:
        result = subprocess.run(
            ['gst-device-monitor-1.0', 'Video'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print(result.stdout)
        
    except FileNotFoundError:
        logger.error("gst-device-monitor-1.0 nicht gefunden")
        logger.error("Installation: brew install gstreamer (macOS) oder apt-get install gstreamer1.0-tools (Linux)")
    except Exception as e:
        logger.error(f"Fehler beim Auflisten der Devices: {e}")


def test_decklink_pipeline(device_number: int = 0, connection: str = "sdi"):
    """
    Testet DeckLink-Pipeline mit gst-launch
    
    Args:
        device_number: DeckLink Device-Nummer
        connection: Verbindungstyp (sdi, hdmi, etc.)
    """
    if not GST_AVAILABLE:
        logger.error("GStreamer nicht verfügbar")
        return
    
    import subprocess
    
    pipeline = (
        f"gst-launch-1.0 decklinkvideosrc device-number={device_number} "
        f"connection={connection} mode=1080p25 ! videoconvert ! autovideosink"
    )
    
    logger.info(f"Teste DeckLink-Pipeline: {pipeline}")
    logger.info("Drücke Ctrl+C zum Beenden")
    
    try:
        subprocess.run(pipeline.split(), check=True)
    except KeyboardInterrupt:
        logger.info("Test beendet")
    except Exception as e:
        logger.error(f"Pipeline-Test fehlgeschlagen: {e}")


if __name__ == "__main__":
    # Test-Code
    logger.info("GStreamer Handler Test")
    logger.info("=" * 60)
    
    # Verfügbare Devices auflisten
    list_gstreamer_devices()
    
    # Test mit DeckLink (wenn vorhanden)
    # test_decklink_pipeline(device_number=0, connection="sdi")
