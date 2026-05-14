#!/usr/bin/env python3
"""
Detection Example
Demonstriert die YOLO-basierte Person Detection
"""

import sys
import cv2
from pathlib import Path

# Sicherstellen dass src im Python-Path ist
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.stream import create_video_source
from src.tracking.person_detector import PersonDetector
from src.utils.logger import setup_logger
from src.utils.performance import FPSCounter


def draw_detections(frame, detections):
    """
    Zeichnet Detections auf Frame
    
    Args:
        frame: Input-Frame
        detections: Liste von Detection-Objekten
    
    Returns:
        Frame mit gezeichneten Detections
    """
    for det in detections:
        # Bounding Box
        cv2.rectangle(
            frame,
            (det.x1, det.y1),
            (det.x2, det.y2),
            (0, 255, 0),  # Grün
            2
        )
        
        # Label mit Confidence
        label = f"Person {det.confidence:.2f}"
        label_size, _ = cv2.getTextSize(
            label,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            2
        )
        
        # Label-Hintergrund
        cv2.rectangle(
            frame,
            (det.x1, det.y1 - label_size[1] - 10),
            (det.x1 + label_size[0], det.y1),
            (0, 255, 0),
            -1
        )
        
        # Label-Text
        cv2.putText(
            frame,
            label,
            (det.x1, det.y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 0),
            2
        )
        
        # Center-Punkt
        center = det.center
        cv2.circle(frame, center, 5, (0, 0, 255), -1)
    
    return frame


def main():
    """
    Hauptfunktion - Person Detection Demo
    """
    # Logger einrichten
    logger = setup_logger("detection_example", level="INFO")
    
    logger.info("=" * 60)
    logger.info("Person Detection Example")
    logger.info("=" * 60)
    
    # Video-Quelle auswählen
    print("\nVerfügbare Video-Quellen:")
    print("  1. Webcam (Standard)")
    print("  2. Video-Datei")
    
    choice = input("\nWähle eine Option (1-2) [1]: ").strip() or "1"
    
    # Video-Quelle erstellen
    try:
        if choice == "1":
            video_source = create_video_source("webcam", camera_index=0)
        elif choice == "2":
            file_path = input("Pfad zur Video-Datei: ").strip()
            if not file_path:
                logger.error("Kein Pfad angegeben")
                return 1
            video_source = create_video_source("file", file_path=file_path, loop=True)
        else:
            logger.error("Ungültige Auswahl")
            return 1
    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Video-Quelle: {e}")
        return 1
    
    # Video-Quelle öffnen
    logger.info("\nÖffne Video-Quelle...")
    if not video_source.open():
        logger.error("Video-Quelle konnte nicht geöffnet werden")
        return 1
    
    # Person Detector erstellen und laden
    logger.info("\nInitialisiere Person Detector...")
    detector = PersonDetector()
    detector.load_model()
    
    # FPS-Counter
    fps_counter = FPSCounter()
    
    # OpenCV-Window erstellen
    window_name = "Person Detection (q=Quit, Space=Pause)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1280, 720)
    
    logger.info("\n" + "=" * 60)
    logger.info("Detection läuft...")
    logger.info("  q = Beenden")
    logger.info("  Space = Pause/Resume")
    logger.info("=" * 60)
    
    paused = False
    frame_count = 0
    total_detections = 0
    
    try:
        while True:
            if not paused:
                # Frame lesen
                success, frame = video_source.read()
                
                if not success:
                    logger.warning("Frame konnte nicht gelesen werden")
                    break
                
                frame_count += 1
                fps_counter.update()
                
                # Person Detection durchführen
                detections = detector.detect(frame)
                total_detections += len(detections)
                
                # Detections zeichnen
                frame = draw_detections(frame, detections)
                
                # Info-Text
                info_lines = [
                    f"FPS: {fps_counter.get_fps():.1f}",
                    f"Frame: {frame_count}",
                    f"Personen: {len(detections)}",
                    f"Total: {total_detections}"
                ]
                
                y_offset = 30
                for line in info_lines:
                    cv2.putText(
                        frame,
                        line,
                        (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2
                    )
                    y_offset += 30
            
            # Frame anzeigen
            cv2.imshow(window_name, frame)
            
            # Key-Events
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                logger.info("\nBeenden durch Benutzer...")
                break
            elif key == ord(' '):
                paused = not paused
                status = "pausiert" if paused else "fortgesetzt"
                logger.info(f"Stream {status}")
    
    except KeyboardInterrupt:
        logger.info("\nBeenden durch Ctrl+C...")
    
    except Exception as e:
        logger.exception(f"Fehler in Hauptschleife: {e}")
    
    finally:
        # Aufräumen
        logger.info("\nSchließe Video-Quelle...")
        video_source.release()
        cv2.destroyAllWindows()
        
        # Statistiken
        logger.info("\n" + "=" * 60)
        logger.info("Statistiken:")
        logger.info(f"  Frames: {frame_count}")
        logger.info(f"  Total Detections: {total_detections}")
        logger.info(f"  Durchschnitt FPS: {fps_counter.get_average_fps():.1f}")
        logger.info(f"  Laufzeit: {fps_counter.get_elapsed_time():.1f}s")
        if frame_count > 0:
            logger.info(f"  Detections/Frame: {total_detections/frame_count:.2f}")
        logger.info("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
