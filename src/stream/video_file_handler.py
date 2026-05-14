"""
Video File Handler
Verarbeitet Video-Dateien für Testing
"""

import cv2
import numpy as np
from typing import Optional, Tuple
from pathlib import Path

from src.utils.logger import get_logger
from src import config
from src.stream.video_source import VideoSource


logger = get_logger(__name__)


class VideoFileHandler(VideoSource):
    """
    Verarbeitet Video-Dateien über OpenCV
    """
    
    def __init__(self, file_path: str, loop: bool = True):
        """
        Args:
            file_path: Pfad zur Video-Datei
            loop: Video in Schleife abspielen
        """
        super().__init__()
        
        self.file_path = Path(file_path)
        self.loop = loop
        
        self.capture = None
        self.total_frames = 0
        self.current_frame = 0
        self.resolution = None
        self.fps = None
        
        logger.info(f"Video File Handler initialisiert")
        logger.info(f"Datei: {self.file_path}")
        logger.info(f"Loop: {self.loop}")
    
    def open(self) -> bool:
        """
        Öffnet die Video-Datei
        
        Returns:
            True wenn erfolgreich
        """
        try:
            # Prüfen ob Datei existiert
            if not self.file_path.exists():
                logger.error(f"Video-Datei nicht gefunden: {self.file_path}")
                return False
            
            logger.info(f"Öffne Video-Datei: {self.file_path.name}...")
            
            # Video öffnen
            self.capture = cv2.VideoCapture(str(self.file_path))
            
            if not self.capture.isOpened():
                logger.error("Video-Datei konnte nicht geöffnet werden")
                return False
            
            # Video-Eigenschaften auslesen
            self.resolution = (
                int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            )
            self.fps = self.capture.get(cv2.CAP_PROP_FPS)
            self.total_frames = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))
            
            logger.info(f"✓ Video geöffnet")
            logger.info(f"  Auflösung: {self.resolution[0]}x{self.resolution[1]}")
            logger.info(f"  FPS: {self.fps:.1f}")
            logger.info(f"  Frames: {self.total_frames}")
            logger.info(f"  Dauer: {self.total_frames / self.fps:.1f}s")
            
            self.is_opened = True
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Öffnen der Video-Datei: {e}")
            return False
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Liest einen Frame von der Video-Datei
        
        Returns:
            (success, frame)
        """
        if not self.is_opened or self.capture is None:
            return False, None
        
        try:
            success, frame = self.capture.read()
            
            if success:
                self.frame_count += 1
                self.current_frame += 1
            else:
                # Ende des Videos erreicht
                if self.loop:
                    # Von vorne beginnen
                    logger.debug("Video-Ende erreicht, starte von vorne...")
                    self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.current_frame = 0
                    success, frame = self.capture.read()
                    if success:
                        self.frame_count += 1
                        self.current_frame += 1
                else:
                    logger.info("Video-Ende erreicht")
            
            return success, frame
            
        except Exception as e:
            logger.error(f"Fehler beim Frame-Lesen: {e}")
            return False, None
    
    def release(self):
        """
        Gibt Video-Ressourcen frei
        """
        if self.capture is not None:
            self.capture.release()
            self.capture = None
        
        self.is_opened = False
        logger.info("Video-Datei geschlossen")
    
    def get_resolution(self) -> Tuple[int, int]:
        """Returns: (width, height)"""
        return self.resolution or config.RESOLUTION
    
    def get_fps(self) -> float:
        """Returns: FPS"""
        return self.fps or float(config.FPS_TARGET)
    
    def get_progress(self) -> float:
        """
        Returns:
            Fortschritt in Prozent (0.0 - 100.0)
        """
        if self.total_frames > 0:
            return (self.current_frame / self.total_frames) * 100.0
        return 0.0


if __name__ == "__main__":
    # Test
    import sys
    
    logger.info("Testing Video File Handler...")
    logger.info("-" * 60)
    
    if len(sys.argv) > 1:
        video_file = sys.argv[1]
    else:
        logger.warning("Kein Video-Datei angegeben")
        logger.info("Verwendung: python video_file_handler.py <pfad_zur_video.mp4>")
        sys.exit(1)
    
    handler = VideoFileHandler(video_file, loop=False)
    
    if handler.open():
        logger.info("Lese erste 10 Frames...")
        
        for i in range(10):
            success, frame = handler.read()
            if success:
                logger.info(f"Frame {i+1}: {frame.shape} - Progress: {handler.get_progress():.1f}%")
            else:
                logger.warning(f"Frame {i+1}: Ende oder Fehler")
                break
        
        handler.release()
        logger.info("✓ Test erfolgreich")
    else:
        logger.error("✗ Video konnte nicht geöffnet werden")
    
    logger.info("-" * 60)
