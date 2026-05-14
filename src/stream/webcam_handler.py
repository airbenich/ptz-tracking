"""
Webcam Handler
OpenCV-basierter Webcam-Input für Development/Testing
"""

import cv2
import numpy as np
from typing import Optional, Tuple

from src.utils.logger import get_logger
from src import config
from src.stream.video_source import VideoSource


logger = get_logger(__name__)


class WebcamHandler(VideoSource):
    """
    Verarbeitet Webcam-Input über OpenCV
    """
    
    def __init__(
        self,
        camera_index: int = 0,
        resolution: Optional[Tuple[int, int]] = None,
        fps: Optional[int] = None
    ):
        """
        Args:
            camera_index: Index der Webcam (0 = Standard)
            resolution: Optional (width, height) - wenn None, nutze Kamera-Standard
            fps: Optional FPS - wenn None, nutze Kamera-Standard
        """
        super().__init__()
        
        self.camera_index = camera_index
        self.target_resolution = resolution
        self.target_fps = fps
        
        self.capture = None
        self.actual_resolution = None
        self.actual_fps = None
        
        logger.info(f"Webcam Handler initialisiert: Index {camera_index}")
        if resolution:
            logger.info(f"Ziel-Auflösung: {resolution[0]}x{resolution[1]}")
        if fps:
            logger.info(f"Ziel-FPS: {fps}")
    
    def open(self) -> bool:
        """
        Öffnet die Webcam
        
        Returns:
            True wenn erfolgreich
        """
        try:
            logger.info(f"Öffne Webcam {self.camera_index}...")
            
            # Webcam öffnen
            self.capture = cv2.VideoCapture(self.camera_index)
            
            if not self.capture.isOpened():
                logger.error("Webcam konnte nicht geöffnet werden")
                return False
            
            # Auflösung setzen (falls angegeben)
            if self.target_resolution:
                self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_resolution[0])
                self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_resolution[1])
            
            # FPS setzen (falls angegeben)
            if self.target_fps:
                self.capture.set(cv2.CAP_PROP_FPS, self.target_fps)
            
            # Tatsächliche Werte auslesen
            self.actual_resolution = (
                int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            )
            self.actual_fps = self.capture.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"✓ Webcam geöffnet")
            logger.info(f"  Auflösung: {self.actual_resolution[0]}x{self.actual_resolution[1]}")
            logger.info(f"  FPS: {self.actual_fps:.1f}")
            
            self.is_opened = True
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Öffnen der Webcam: {e}")
            return False
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Liest einen Frame von der Webcam
        
        Returns:
            (success, frame)
        """
        if not self.is_opened or self.capture is None:
            return False, None
        
        try:
            success, frame = self.capture.read()
            
            if success:
                self.frame_count += 1
            
            return success, frame
            
        except Exception as e:
            logger.error(f"Fehler beim Frame-Lesen: {e}")
            return False, None
    
    def release(self):
        """
        Gibt Webcam-Ressourcen frei
        """
        if self.capture is not None:
            self.capture.release()
            self.capture = None
        
        self.is_opened = False
        logger.info("Webcam geschlossen")
    
    def get_resolution(self) -> Tuple[int, int]:
        """Returns: (width, height)"""
        if self.actual_resolution:
            return self.actual_resolution
        return self.target_resolution or config.RESOLUTION
    
    def get_fps(self) -> float:
        """Returns: FPS"""
        if self.actual_fps:
            return self.actual_fps
        return float(self.target_fps or config.FPS_TARGET)


if __name__ == "__main__":
    # Test
    import time
    
    logger.info("Testing Webcam Handler...")
    logger.info("-" * 60)
    
    handler = WebcamHandler(camera_index=0)
    
    if handler.open():
        logger.info("Lese 10 Frames...")
        
        for i in range(10):
            success, frame = handler.read()
            if success:
                logger.info(f"Frame {i+1}: {frame.shape}")
                time.sleep(0.1)
            else:
                logger.warning(f"Frame {i+1}: Fehler beim Lesen")
        
        handler.release()
        logger.info("✓ Test erfolgreich")
    else:
        logger.error("✗ Webcam konnte nicht geöffnet werden")
    
    logger.info("-" * 60)
