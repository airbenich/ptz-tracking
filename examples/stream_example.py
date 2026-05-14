#!/usr/bin/env python3
"""
Stream-Handler Beispiel
Demonstriert die Verwendung der verschiedenen Video-Input-Handler
"""

import sys
import cv2
from pathlib import Path

# Sicherstellen dass src im Python-Path ist
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.stream import create_video_source
from src.utils.logger import setup_logger
from src.utils.performance import FPSCounter


def main():
    """
    Hauptfunktion - zeigt Video-Stream mit FPS-Counter an
    """
    # Logger einrichten
    logger = setup_logger("stream_example", level="INFO")
    
    logger.info("=" * 60)
    logger.info("Stream-Handler Beispiel")
    logger.info("=" * 60)
    
    # Video-Quelle auswählen
    print("\nVerfügbare Video-Quellen:")
    print("  1. Webcam (Standard)")
    print("  2. Video-Datei")
    print("  3. FFmpeg (Blackmagic/Elgato)")
    
    choice = input("\nWähle eine Option (1-3) [1]: ").strip() or "1"
    
    # Video-Quelle erstellen
    try:
        if choice == "1":
            # Webcam
            video_source = create_video_source("webcam", camera_index=0)
        
        elif choice == "2":
            # Video-Datei
            file_path = input("Pfad zur Video-Datei: ").strip()
            if not file_path:
                logger.error("Kein Pfad angegeben")
                return 1
            video_source = create_video_source("file", file_path=file_path, loop=True)
        
        elif choice == "3":
            # FFmpeg
            logger.warning("FFmpeg benötigt ein aktives Video-Device (Blackmagic/Elgato)")
            video_source = create_video_source("ffmpeg")
        
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
        logger.info("\nTipps:")
        logger.info("  - Bei Webcam: Kamera-Berechtigung in Systemeinstellungen prüfen")
        logger.info("  - Bei File: Pfad korrekt?")
        logger.info("  - Bei FFmpeg: ffmpeg installiert? Device verbunden?")
        return 1
    
    # FPS-Counter
    fps_counter = FPSCounter()
    
    # OpenCV-Window erstellen
    window_name = "Stream Example (Drücke 'q' zum Beenden)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1280, 720)
    
    logger.info("\n" + "=" * 60)
    logger.info("Stream läuft - Drücke 'q' zum Beenden")
    logger.info("=" * 60)
    
    try:
        frame_count = 0
        
        while True:
            # Frame lesen
            success, frame = video_source.read()
            
            if not success:
                logger.warning("Frame konnte nicht gelesen werden")
                break
            
            frame_count += 1
            fps_counter.update()
            
            # FPS auf Frame zeichnen
            fps_text = f"FPS: {fps_counter.get_fps():.1f} | Frame: {frame_count}"
            cv2.putText(
                frame,
                fps_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 255, 0),
                2
            )
            
            # Frame anzeigen
            cv2.imshow(window_name, frame)
            
            # Key-Events
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                logger.info("\nBeenden durch Benutzer...")
                break
            elif key == ord('f'):
                # Vollbild-Toggle
                logger.info("Vollbild-Modus...")
                cv2.setWindowProperty(
                    window_name,
                    cv2.WND_PROP_FULLSCREEN,
                    cv2.WINDOW_FULLSCREEN
                )
    
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
        logger.info(f"  Durchschnitt FPS: {fps_counter.get_average_fps():.1f}")
        logger.info(f"  Laufzeit: {fps_counter.get_elapsed_time():.1f}s")
        logger.info("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
