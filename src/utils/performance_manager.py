"""
Performance Manager
Dynamische Performance-Optimierung basierend auf Systemlast
"""

import time
from typing import Optional
from collections import deque

from src.utils.logger import get_logger
from src import config


logger = get_logger(__name__)


class PerformanceManager:
    """
    Verwaltet Performance-Optimierungen wie Frame-Skipping
    """
    
    def __init__(
        self,
        target_fps: float = None,
        enable_frame_skip: bool = True,
        skip_threshold: float = 0.7
    ):
        """
        Args:
            target_fps: Ziel-FPS (aus config wenn None)
            enable_frame_skip: Frame-Skipping aktivieren
            skip_threshold: Schwellwert für Frame-Skip (0.0-1.0)
                           Bei Performance < threshold * target_fps wird geskippt
        """
        self.target_fps = target_fps or config.FPS_TARGET
        self.enable_frame_skip = enable_frame_skip
        self.skip_threshold = skip_threshold
        
        # Performance-Tracking
        self.frame_times = deque(maxlen=30)  # Letzte 30 Frame-Zeiten
        self.last_frame_time = time.time()
        
        # Statistiken
        self.total_frames = 0
        self.processed_frames = 0
        self.skipped_frames = 0
        
        # Adaptive Skip-Rate
        self.current_skip_rate = 0  # 0 = kein Skip, 1 = jeden 2., 2 = jeden 3., etc.
        
        logger.info(f"PerformanceManager initialisiert")
        logger.info(f"  Target FPS: {self.target_fps}")
        logger.info(f"  Frame-Skip: {self.enable_frame_skip}")
        logger.info(f"  Skip-Threshold: {skip_threshold * 100:.0f}%")
    
    def should_process_frame(self) -> bool:
        """
        Entscheidet ob aktueller Frame verarbeitet werden soll
        
        Returns:
            True wenn Frame verarbeitet werden soll
        """
        self.total_frames += 1
        
        if not self.enable_frame_skip:
            self.processed_frames += 1
            return True
        
        # Performance berechnen
        current_fps = self.get_current_fps()
        target_threshold = self.target_fps * self.skip_threshold
        
        # Adaptive Skip-Rate anpassen
        if current_fps < target_threshold:
            # Performance zu niedrig - Skip-Rate erhöhen
            if self.current_skip_rate < 3:  # Max jeden 4. Frame skippen
                self.current_skip_rate += 1
                logger.debug(f"Performance niedrig ({current_fps:.1f} FPS) - Skip-Rate erhöht auf {self.current_skip_rate}")
        
        elif current_fps > self.target_fps * 0.9:
            # Performance gut - Skip-Rate verringern
            if self.current_skip_rate > 0:
                self.current_skip_rate -= 1
                logger.debug(f"Performance gut ({current_fps:.1f} FPS) - Skip-Rate verringert auf {self.current_skip_rate}")
        
        # Frame-Skip-Entscheidung
        if self.current_skip_rate > 0:
            # Jeden N-ten Frame skippen
            skip_pattern = self.current_skip_rate + 1
            should_skip = (self.total_frames % skip_pattern) != 0
            
            if should_skip:
                self.skipped_frames += 1
                return False
        
        self.processed_frames += 1
        return True
    
    def update_frame_time(self):
        """
        Aktualisiert Frame-Zeit für Performance-Tracking
        """
        current_time = time.time()
        frame_time = current_time - self.last_frame_time
        self.frame_times.append(frame_time)
        self.last_frame_time = current_time
    
    def get_current_fps(self) -> float:
        """
        Berechnet aktuelle FPS basierend auf letzten Frame-Zeiten
        
        Returns:
            Aktuelle FPS
        """
        if len(self.frame_times) < 2:
            return 0.0
        
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        
        if avg_frame_time > 0:
            return 1.0 / avg_frame_time
        
        return 0.0
    
    def get_statistics(self) -> dict:
        """
        Gibt Performance-Statistiken zurück
        
        Returns:
            Dictionary mit Statistiken
        """
        skip_rate = (self.skipped_frames / self.total_frames * 100) if self.total_frames > 0 else 0
        
        return {
            'total_frames': self.total_frames,
            'processed_frames': self.processed_frames,
            'skipped_frames': self.skipped_frames,
            'skip_rate': skip_rate,
            'current_fps': self.get_current_fps(),
            'target_fps': self.target_fps,
            'current_skip_pattern': self.current_skip_rate
        }
    
    def reset(self):
        """
        Setzt Statistiken zurück
        """
        self.total_frames = 0
        self.processed_frames = 0
        self.skipped_frames = 0
        self.current_skip_rate = 0
        self.frame_times.clear()
        self.last_frame_time = time.time()
        
        logger.debug("PerformanceManager zurückgesetzt")


if __name__ == "__main__":
    # Test
    import random
    
    logger.info("=" * 60)
    logger.info("Testing PerformanceManager...")
    logger.info("=" * 60)
    
    # Manager erstellen
    manager = PerformanceManager(
        target_fps=30,
        enable_frame_skip=True,
        skip_threshold=0.7
    )
    
    logger.info("\nSimuliere verschiedene Performance-Szenarien:\n")
    
    # Szenario 1: Gute Performance
    logger.info("1. Szenario: Gute Performance (30 FPS)")
    for i in range(100):
        time.sleep(1.0 / 30.0)  # Simuliere 30 FPS
        if manager.should_process_frame():
            manager.update_frame_time()
    
    stats = manager.get_statistics()
    logger.info(f"   Verarbeitet: {stats['processed_frames']}/100")
    logger.info(f"   Skip-Rate: {stats['skip_rate']:.1f}%")
    logger.info(f"   Current FPS: {stats['current_fps']:.1f}")
    
    # Reset
    manager.reset()
    
    # Szenario 2: Schlechte Performance
    logger.info("\n2. Szenario: Schlechte Performance (15 FPS)")
    for i in range(100):
        time.sleep(1.0 / 15.0)  # Simuliere 15 FPS
        if manager.should_process_frame():
            manager.update_frame_time()
    
    stats = manager.get_statistics()
    logger.info(f"   Verarbeitet: {stats['processed_frames']}/100")
    logger.info(f"   Skip-Rate: {stats['skip_rate']:.1f}%")
    logger.info(f"   Current FPS: {stats['current_fps']:.1f}")
    
    # Reset
    manager.reset()
    
    # Szenario 3: Schwankende Performance
    logger.info("\n3. Szenario: Schwankende Performance")
    for i in range(100):
        # Zufällige Frame-Zeit zwischen 20-40 FPS
        fps = random.uniform(20, 40)
        time.sleep(1.0 / fps)
        if manager.should_process_frame():
            manager.update_frame_time()
    
    stats = manager.get_statistics()
    logger.info(f"   Verarbeitet: {stats['processed_frames']}/100")
    logger.info(f"   Skip-Rate: {stats['skip_rate']:.1f}%")
    logger.info(f"   Current FPS: {stats['current_fps']:.1f}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ PerformanceManager Tests abgeschlossen")
    logger.info("=" * 60)
