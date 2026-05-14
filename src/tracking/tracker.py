"""
Person Tracker
Frame-zu-Frame Tracking der prominentesten Person
"""

from typing import Optional, List
import numpy as np

from src.utils.logger import get_logger
from src.tracking.person_detector import Detection
from src import config


logger = get_logger(__name__)


class PersonTracker:
    """
    Verfolgt die prominenteste Person über mehrere Frames
    """
    
    def __init__(
        self,
        tracking_method: str = None,
        smoothing_enabled: bool = None,
        smoothing_factor: float = None
    ):
        """
        Args:
            tracking_method: "largest_bbox", "most_centered", "highest_confidence"
            smoothing_enabled: Smoothing aktivieren
            smoothing_factor: Smoothing-Faktor (0.0 - 1.0)
        """
        self.tracking_method = tracking_method or config.TRACKING_METHOD
        self.smoothing_enabled = smoothing_enabled if smoothing_enabled is not None else config.SMOOTHING_ENABLED
        self.smoothing_factor = smoothing_factor or config.SMOOTHING_FACTOR
        
        self.current_detection: Optional[Detection] = None
        self.smoothed_bbox: Optional[tuple] = None
        self.frames_without_detection = 0
        
        logger.info(f"Person Tracker initialisiert")
        logger.info(f"Methode: {self.tracking_method}")
        logger.info(f"Smoothing: {self.smoothing_enabled} (Factor: {self.smoothing_factor})")
    
    def update(self, detections: List[Detection], frame_shape: tuple) -> Optional[Detection]:
        """
        Aktualisiert Tracking mit neuen Detections
        
        Args:
            detections: Liste von Person Detections
            frame_shape: (height, width, channels)
        
        Returns:
            Beste Detection oder None
        """
        if not detections:
            self.frames_without_detection += 1
            
            if self.frames_without_detection > config.MAX_FRAMES_WITHOUT_DETECTION:
                self.reset()
            
            return self.current_detection
        
        # Beste Detection auswählen
        best_detection = self._select_best_detection(detections, frame_shape)
        
        # Smoothing anwenden
        if self.smoothing_enabled and self.current_detection:
            best_detection = self._apply_smoothing(best_detection)
        
        self.current_detection = best_detection
        self.frames_without_detection = 0
        
        return best_detection
    
    def _select_best_detection(
        self,
        detections: List[Detection],
        frame_shape: tuple
    ) -> Detection:
        """
        Wählt die beste Detection basierend auf tracking_method
        
        Args:
            detections: Liste von Detections
            frame_shape: (height, width, channels)
        
        Returns:
            Beste Detection
        """
        if self.tracking_method == "largest_bbox":
            # Größte Bounding Box
            return max(detections, key=lambda d: d.area)
        
        elif self.tracking_method == "most_centered":
            # Am meisten zentrierte Person
            frame_center = (frame_shape[1] // 2, frame_shape[0] // 2)
            
            def distance_to_center(det: Detection) -> float:
                cx, cy = det.center
                dx = cx - frame_center[0]
                dy = cy - frame_center[1]
                return (dx**2 + dy**2) ** 0.5
            
            return min(detections, key=distance_to_center)
        
        elif self.tracking_method == "highest_confidence":
            # Höchste Konfidenz
            return max(detections, key=lambda d: d.confidence)
        
        else:
            logger.warning(f"Unbekannte Tracking-Methode: {self.tracking_method}")
            return detections[0]
    
    def _apply_smoothing(self, detection: Detection) -> Detection:
        """
        Wendet Smoothing auf Bounding Box an
        
        Args:
            detection: Neue Detection
        
        Returns:
            Detection mit geglätteter Bounding Box
        """
        if not self.smoothed_bbox:
            self.smoothed_bbox = detection.bbox
            return detection
        
        # Exponential Smoothing
        alpha = 1 - self.smoothing_factor
        
        smoothed = tuple(
            int(alpha * new + (1 - alpha) * old)
            for new, old in zip(detection.bbox, self.smoothed_bbox)
        )
        
        self.smoothed_bbox = smoothed
        
        return Detection(
            bbox=smoothed,
            confidence=detection.confidence,
            class_id=detection.class_id,
            keypoints=detection.keypoints  # Keypoints übernehmen
        )
    
    def reset(self):
        """
        Setzt Tracker zurück
        """
        self.current_detection = None
        self.smoothed_bbox = None
        self.frames_without_detection = 0
        logger.debug("Tracker zurückgesetzt")
    
    def get_current_detection(self) -> Optional[Detection]:
        """
        Returns:
            Aktuelle Detection oder None
        """
        return self.current_detection


if __name__ == "__main__":
    # Test
    logger.info("=" * 60)
    logger.info("Testing Person Tracker...")
    logger.info("=" * 60)
    
    frame_shape = (720, 1280, 3)
    
    # Test-Detections erstellen
    # Person 1: Links, groß, hohe Konfidenz
    # Person 2: Mitte, mittel, mittlere Konfidenz
    # Person 3: Rechts, klein, niedrige Konfidenz
    detections = [
        Detection(bbox=(100, 100, 400, 600), confidence=0.9),   # Links, groß
        Detection(bbox=(500, 200, 700, 500), confidence=0.7),   # Mitte
        Detection(bbox=(900, 300, 1000, 450), confidence=0.5),  # Rechts, klein
    ]
    
    logger.info(f"\nTest-Detections: {len(detections)}")
    for i, det in enumerate(detections):
        logger.info(f"  {i+1}. {det} | Area: {det.area} | Center: {det.center}")
    
    # Test 1: largest_bbox
    logger.info("\n1. Test: largest_bbox")
    tracker1 = PersonTracker(tracking_method="largest_bbox")
    best1 = tracker1.update(detections, frame_shape)
    logger.info(f"   Beste: {best1} (erwartet: größte)")
    
    # Test 2: most_centered
    logger.info("\n2. Test: most_centered")
    tracker2 = PersonTracker(tracking_method="most_centered")
    best2 = tracker2.update(detections, frame_shape)
    logger.info(f"   Beste: {best2} (erwartet: in der Mitte)")
    
    # Test 3: highest_confidence
    logger.info("\n3. Test: highest_confidence")
    tracker3 = PersonTracker(tracking_method="highest_confidence")
    best3 = tracker3.update(detections, frame_shape)
    logger.info(f"   Beste: {best3} (erwartet: höchste Konfidenz)")
    
    # Test 4: Smoothing
    logger.info("\n4. Test: Smoothing")
    tracker4 = PersonTracker(
        tracking_method="largest_bbox",
        smoothing_enabled=True,
        smoothing_factor=0.5
    )
    
    # Frame 1
    det1 = Detection(bbox=(100, 100, 300, 400), confidence=0.9)
    result1 = tracker4.update([det1], frame_shape)
    logger.info(f"   Frame 1: {result1.bbox}")
    
    # Frame 2 - leicht verschoben
    det2 = Detection(bbox=(120, 110, 320, 410), confidence=0.9)
    result2 = tracker4.update([det2], frame_shape)
    logger.info(f"   Frame 2: {result2.bbox} (sollte geglättet sein)")
    
    # Test 5: Tracking Loss
    logger.info("\n5. Test: Tracking Loss")
    tracker5 = PersonTracker()
    tracker5.update([detections[0]], frame_shape)
    logger.info(f"   Initial: {tracker5.current_detection}")
    
    # Mehrere Frames ohne Detection
    for i in range(config.MAX_FRAMES_WITHOUT_DETECTION + 1):
        tracker5.update([], frame_shape)
    
    logger.info(f"   Nach {config.MAX_FRAMES_WITHOUT_DETECTION + 1} Frames: {tracker5.current_detection}")
    logger.info(f"   (sollte None sein)")
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ Tracker Tests abgeschlossen")
    logger.info("=" * 60)
