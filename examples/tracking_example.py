#!/usr/bin/env python3
"""
Tracking Example
Demonstriert die komplette PTZ Tracking Pipeline
Stream → Detection → Tracking → Visualisierung
"""

import sys
import cv2
from pathlib import Path

# Sicherstellen dass src im Python-Path ist
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.stream import create_video_source
from src.tracking.person_detector import PersonDetector
from src.tracking.tracker import PersonTracker
from src.display.visualizer import Visualizer
from src.utils.logger import setup_logger


def main():
    """
    Hauptfunktion - Komplette Tracking Pipeline Demo
    """
    # Logger einrichten
    logger = setup_logger("tracking_example", level="INFO")
    
    logger.info("=" * 60)
    logger.info("PTZ Tracking Pipeline Example")
    logger.info("=" * 60)
    
    # Video-Quelle auswählen
    print("\nVerfügbare Video-Quellen:")
    print("  1. Webcam (Standard)")
    print("  2. Video-Datei")
    
    choice = input("\nWähle eine Option (1-2) [1]: ").strip() or "1"
    
    # Tracking-Methode auswählen
    print("\nTracking-Methoden:")
    print("  1. Largest BBox (Standard) - Größte Person")
    print("  2. Most Centered - Person am nächsten zur Bildmitte")
    print("  3. Highest Confidence - Person mit höchster Konfidenz")
    
    method_choice = input("\nWähle Methode (1-3) [1]: ").strip() or "1"
    
    tracking_methods = {
        "1": "largest_bbox",
        "2": "most_centered",
        "3": "highest_confidence"
    }
    tracking_method = tracking_methods.get(method_choice, "largest_bbox")
    
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
    
    # Tracker erstellen
    logger.info(f"\nInitialisiere Tracker (Methode: {tracking_method})...")
    tracker = PersonTracker(tracking_method=tracking_method)
    
    # Visualizer erstellen
    logger.info("\nInitialisiere Visualizer...")
    visualizer = Visualizer()
    visualizer.create_window()
    
    logger.info("\n" + "=" * 60)
    logger.info("Tracking läuft...")
    logger.info("  q = Beenden")
    logger.info("  Space = Pause/Resume")
    logger.info("  r = Tracker zurücksetzen")
    logger.info("=" * 60)
    
    paused = False
    frame_count = 0
    total_detections = 0
    tracked_frames = 0
    
    try:
        while True:
            if not paused:
                # Frame lesen
                success, frame = video_source.read()
                
                if not success:
                    logger.warning("Frame konnte nicht gelesen werden")
                    break
                
                frame_count += 1
                
                # Person Detection durchführen
                detections = detector.detect(frame)
                total_detections += len(detections)
                
                # Tracking aktualisieren
                tracked_detection = tracker.update(detections, frame.shape)
                
                if tracked_detection:
                    tracked_frames += 1
                
                # Visualisierung
                key = visualizer.show(frame, tracked_detection)
                
                # Key-Events
                if key == ord('q'):
                    logger.info("\nBeenden durch Benutzer...")
                    break
                elif key == ord(' '):
                    paused = not paused
                    status = "pausiert" if paused else "fortgesetzt"
                    logger.info(f"Stream {status}")
                elif key == ord('r'):
                    logger.info("Tracker zurückgesetzt")
                    tracker.reset()
            else:
                # Im Pause-Modus nur auf Tasteneingaben warten
                key = cv2.waitKey(100) & 0xFF
                if key == ord('q'):
                    logger.info("\nBeenden durch Benutzer...")
                    break
                elif key == ord(' '):
                    paused = False
                    logger.info("Stream fortgesetzt")
    
    except KeyboardInterrupt:
        logger.info("\nBeenden durch Ctrl+C...")
    
    except Exception as e:
        logger.exception(f"Fehler in Hauptschleife: {e}")
    
    finally:
        # Aufräumen
        logger.info("\nSchließe Anwendung...")
        video_source.release()
        visualizer.destroy()
        
        # Statistiken
        logger.info("\n" + "=" * 60)
        logger.info("Statistiken:")
        logger.info(f"  Frames gesamt: {frame_count}")
        logger.info(f"  Total Detections: {total_detections}")
        logger.info(f"  Frames mit Tracking: {tracked_frames}")
        if frame_count > 0:
            logger.info(f"  Tracking-Rate: {tracked_frames/frame_count*100:.1f}%")
            logger.info(f"  Detections/Frame: {total_detections/frame_count:.2f}")
        logger.info(f"  Durchschnitt FPS: {visualizer.fps_counter.get_average_fps():.1f}")
        logger.info(f"  Laufzeit: {visualizer.fps_counter.get_elapsed_time():.1f}s")
        logger.info("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
