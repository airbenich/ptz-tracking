"""
Video-Quelle - Abstrakte Basisklasse
Einheitliches Interface für verschiedene Video-Inputs
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
import numpy as np


class VideoSource(ABC):
    """
    Abstrakte Basisklasse für Video-Quellen
    """
    
    def __init__(self):
        self.is_opened = False
        self.frame_count = 0
    
    @abstractmethod
    def open(self) -> bool:
        """
        Öffnet die Video-Quelle
        
        Returns:
            True wenn erfolgreich, False sonst
        """
        pass
    
    @abstractmethod
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Liest einen Frame von der Video-Quelle
        
        Returns:
            Tuple (success, frame)
            - success: True wenn Frame erfolgreich gelesen
            - frame: NumPy-Array (BGR) oder None
        """
        pass
    
    @abstractmethod
    def release(self):
        """
        Gibt Ressourcen frei und schließt die Quelle
        """
        pass
    
    @abstractmethod
    def get_resolution(self) -> Tuple[int, int]:
        """
        Returns:
            Tuple (width, height)
        """
        pass
    
    @abstractmethod
    def get_fps(self) -> float:
        """
        Returns:
            Frames pro Sekunde
        """
        pass
    
    def __enter__(self):
        """Context Manager Support"""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager Support"""
        self.release()
        return False
