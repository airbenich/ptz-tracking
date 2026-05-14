#!/usr/bin/env python3
"""
Pose-Estimation Beispiel
Demonstriert Skeleton-Tracking mit YOLOv8-Pose
"""

import sys
import cv2
from pathlib import Path

# Sicherstellen dass src im Python-Path ist
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import config
from src.utils.logger import setup_logger, get_logger
from src.tracking.person_detector import PersonDetector
from src.display.visualizer import Visualizer

# Logging konfigurieren
setup_logger(level="INFO")
logger = get_logger(__name__)


def main():
    """
    Hauptfunktion - Pose-Estimation Demo
    """
    logger.info("=" * 60)
    logger.info("Pose-Estimation Beispiel")
    logger.info("=" * 60)
    
    # Pose-Estimation aktivieren
    config.ENABLE_POSE_ESTIMATION = True
    
    # Webcam initialisieren
    logger.info("\n1. Initialisiere Webcam...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        logger.error("Webcam konnte nicht geöffnet werden!")
        return 1
    
    # Auflösung setzen
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    
    logger.info("✓ Webcam geöffnet")
    
    # Person Detector mit Pose-Estimation
    logger.info("\n2. Initialisiere Person Detector (mit Pose)...")
    detector = PersonDetector(enable_pose=True)
    detector.load_model()
    
    # Visualizer
    logger.info("\n3. Initialisiere Visualizer...")
    visualizer = Visualizer(window_name="Pose-Estimation Demo")
    
    logger.info("\n" + "=" * 60)
    logger.info("Demo läuft...")
    logger.info("  q = Beenden")
    logger.info("  f = Vollbild-Toggle")
    logger.info("=" * 60 + "\n")
    
    # Haupt-Loop
    frame_count = 0
    
    try:
        while True:
            # Frame lesen
            ret, frame = cap.read()
            if not ret:
                logger.warning("Kein Frame empfangen")
                break
            
            frame_count += 1
            
            # Personen erkennen (mit Pose)
            detections = detector.detect(frame)
            
            # Erste Detection verwenden (oder None)
            detection = detections[0] if detections else None
            
            # Visualisierung
            key = visualizer.show(frame, detection)
            
            # Keyboard-Input
            if key == ord('q'):
                logger.info("Beenden...")
                break
            elif key == ord('f'):
                # Vollbild-Toggle
                if visualizer.fullscreen:
                    cv2.setWindowProperty(
                        visualizer.window_name,
                        cv2.WND_PROP_FULLSCREEN,
                        cv2.WINDOW_NORMAL
                    )
                    visualizer.fullscreen = False
                else:
                    cv2.setWindowProperty(
                        visualizer.window_name,
                        cv2.WND_PROP_FULLSCREEN,
                        cv2.WINDOW_FULLSCREEN
                    )
                    visualizer.fullscreen = True
            
            # Status-Output alle 100 Frames
            if frame_count % 100 == 0:
                fps = visualizer.fps_counter.get_fps()
                logger.info(f"Frame {frame_count}: {len(detections)} Personen, {fps:.1f} FPS")
                if detection and detection.has_pose():
                    visible_kpts = detection.get_visible_keypoints()
                    logger.info(f"  → Pose: {len(visible_kpts)}/{len(detection.keypoints)} sichtbare Keypoints")
    
    except KeyboardInterrupt:
        logger.info("\nBeendet durch Benutzer")
    
    finally:
        # Cleanup
        logger.info("\nCleaning up...")
        cap.release()
        cv2.destroyAllWindows()
        
        logger.info(f"\nGesamt: {frame_count} Frames verarbeitet")
        logger.info("Fertig!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
