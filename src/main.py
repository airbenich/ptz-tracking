#!/usr/bin/env python3
"""
PTZ Tracking - Haupteinstiegspunkt
Echtzeit-Tracking von Personen in Videostreams
"""

import sys
import argparse
from pathlib import Path

# Sicherstellen dass src im Python-Path ist
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import config
from src.utils.logger import setup_logger, get_logger


def parse_arguments():
    """
    Kommandozeilen-Argumente parsen
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="PTZ Tracking - Echtzeit Person Tracking in Videostreams",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s                          # Standard-Modus mit Konfiguration aus config.py
  %(prog)s --source webcam          # Webcam-Input für Development
  %(prog)s --source file --file video.mp4   # Video-Datei verarbeiten
  %(prog)s --daemon                 # Als Service/Daemon laufen
  %(prog)s --headless               # Ohne Display (nur Tracking-Daten)
  %(prog)s --debug                  # Debug-Modus
        """
    )
    
    # Video-Source
    parser.add_argument(
        '--source',
        choices=['ffmpeg', 'webcam', 'file'],
        default=config.VIDEO_SOURCE,
        help='Video-Quelle (default: %(default)s)'
    )
    
    parser.add_argument(
        '--device',
        choices=['Blackmagic', 'Elgato', 'Webcam'],
        default=config.FFMPEG_INPUT_DEVICE,
        help='ffmpeg Input-Device (default: %(default)s)'
    )
    
    parser.add_argument(
        '--file',
        type=str,
        help='Pfad zur Video-Datei (wenn --source file)'
    )
    
    # YOLO-Modell
    parser.add_argument(
        '--model',
        type=str,
        default=config.MODEL,
        help='YOLO-Modell (default: %(default)s)'
    )
    
    parser.add_argument(
        '--confidence',
        type=float,
        default=config.CONFIDENCE_THRESHOLD,
        help='Konfidenz-Schwellwert (default: %(default)s)'
    )
    
    # Application Mode
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Als Service/Daemon laufen'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Headless-Modus ohne Display'
    )
    
    parser.add_argument(
        '--no-gpu',
        action='store_true',
        help='GPU-Beschleunigung deaktivieren'
    )
    
    # Logging
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Debug-Modus aktivieren'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        help='Log-Datei Pfad'
    )
    
    # Display
    parser.add_argument(
        '--fullscreen',
        action='store_true',
        help='Vollbild-Modus'
    )
    
    parser.add_argument(
        '--no-display',
        action='store_true',
        help='Kein Display (identisch zu --headless)'
    )
    
    # Performance
    parser.add_argument(
        '--no-threading',
        action='store_true',
        help='Threading für Video-Input deaktivieren'
    )
    
    parser.add_argument(
        '--no-frame-skip',
        action='store_true',
        help='Frame-Skipping deaktivieren'
    )
    
    parser.add_argument(
        '--buffer-size',
        type=int,
        default=config.CAPTURE_BUFFER_SIZE,
        help='Buffer-Größe für threaded capture (default: %(default)s)'
    )
    
    return parser.parse_args()


def apply_cli_args(args):
    """
    Wendet Kommandozeilen-Argumente auf Konfiguration an
    
    Args:
        args: Parsed arguments
    """
    # Video-Source
    config.VIDEO_SOURCE = args.source
    config.FFMPEG_INPUT_DEVICE = args.device
    
    if args.file:
        config.VIDEO_FILE_PATH = args.file
    
    # YOLO
    config.MODEL = args.model
    config.CONFIDENCE_THRESHOLD = args.confidence
    
    # GPU
    if args.no_gpu:
        config.GPU_ENABLED = False
        config.DEVICE = "cpu"
    
    # Application Mode
    if args.daemon:
        config.RUN_AS_SERVICE = True
    
    if args.headless or args.no_display:
        config.HEADLESS_MODE = True
    
    # Logging
    if args.debug:
        config.LOG_LEVEL = "DEBUG"
        config.DEBUG_MODE = True
    
    if args.log_file:
        config.LOG_TO_FILE = True
        config.LOG_FILE = Path(args.log_file)
    
    # Display
    if args.fullscreen:
        config.FULLSCREEN = True
    
    # Performance
    if args.no_threading:
        config.THREADED_CAPTURE = False
    
    if args.no_frame_skip:
        config.ENABLE_FRAME_SKIP = False
    
    if args.buffer_size:
        config.CAPTURE_BUFFER_SIZE = args.buffer_size


def main():
    """
    Haupt-Einstiegspunkt der Anwendung
    """
    # Argumente parsen
    args = parse_arguments()
    apply_cli_args(args)
    
    # Logger einrichten
    logger = setup_logger(
        name="ptz_tracking.main",
        level=config.LOG_LEVEL
    )
    
    logger.info("=" * 60)
    logger.info("PTZ Tracking gestartet")
    logger.info("=" * 60)
    logger.info(f"Video-Source: {config.VIDEO_SOURCE}")
    logger.info(f"Device: {config.FFMPEG_INPUT_DEVICE}")
    logger.info(f"Model: {config.MODEL}")
    logger.info(f"YOLO Device: {config.DEVICE}")
    logger.info(f"Headless: {config.HEADLESS_MODE}")
    logger.info(f"Threading: {config.THREADED_CAPTURE}")
    logger.info(f"Frame-Skip: {config.ENABLE_FRAME_SKIP}")
    logger.info("=" * 60)
    
    # Module importieren
    from src.stream import create_video_source
    from src.stream.threaded_capture import ThreadedVideoCapture
    from src.tracking.person_detector import PersonDetector
    from src.tracking.tracker import PersonTracker
    from src.display.visualizer import Visualizer
    from src.utils.performance_manager import PerformanceManager
    
    # PTZ-Module (wenn aktiviert)
    if config.ENABLE_PTZ:
        from src.ptz import PTZController, PTZRestServer
    
    video_source = None
    threaded_capture = None
    visualizer = None
    ptz_controller = None
    ptz_rest_server = None
    
    # Statistik-Variablen initialisieren (für finally-Block)
    frame_count = 0
    total_detections = 0
    tracked_frames = 0
    paused = False
    perf_manager = None
    
    try:
        # Video-Quelle erstellen
        logger.info("\nInitialisiere Video-Quelle...")
        video_kwargs = {}
        if args.file:
            video_kwargs['file_path'] = args.file
            video_kwargs['loop'] = False  # Keine Loop bei expliziter Datei
        
        video_source = create_video_source(config.VIDEO_SOURCE, **video_kwargs)
        
        # Threading aktivieren wenn konfiguriert
        if config.THREADED_CAPTURE:
            logger.info("Aktiviere Threading für Video-Input...")
            threaded_capture = ThreadedVideoCapture(
                video_source,
                buffer_size=config.CAPTURE_BUFFER_SIZE
            )
            if not threaded_capture.start():
                logger.error("ThreadedVideoCapture konnte nicht gestartet werden")
                return 1
            # threaded_capture als video_source verwenden
            video_capture = threaded_capture
        else:
            # Direkter Zugriff auf video_source
            if not video_source.open():
                logger.error("Video-Quelle konnte nicht geöffnet werden")
                return 1
            video_capture = video_source
        
        # Person Detector initialisieren
        logger.info("Initialisiere Person Detector...")
        detector = PersonDetector(
            confidence_threshold=config.CONFIDENCE_THRESHOLD,
            enable_pose=config.ENABLE_POSE_ESTIMATION
        )
        detector.load_model()
        
        # Tracker initialisieren
        logger.info("Initialisiere Tracker...")
        tracker = PersonTracker()
        
        # PTZ-Controller initialisieren (wenn aktiviert)
        if config.ENABLE_PTZ:
            logger.info("Initialisiere PTZ-Controller...")
            ptz_controller = PTZController()
            
            # REST-Server für PTZ-Steuerung (wenn aktiviert)
            if config.PTZ_REST_ENABLED:
                logger.info("Starte PTZ REST-Server...")
                ptz_rest_server = PTZRestServer(ptz_controller)
                ptz_rest_server.start()
        
        # Performance Manager initialisieren
        if config.ENABLE_FRAME_SKIP:
            logger.info("Initialisiere Performance Manager...")
            perf_manager = PerformanceManager(
                target_fps=config.FPS_TARGET,
                enable_frame_skip=True,
                skip_threshold=config.FRAME_SKIP_THRESHOLD
            )
        else:
            perf_manager = None
        
        # Visualizer initialisieren (wenn nicht headless)
        if not config.HEADLESS_MODE:
            logger.info("Initialisiere Visualizer...")
            visualizer = Visualizer(fullscreen=config.FULLSCREEN)
            visualizer.create_window()
        
        logger.info("\n" + "=" * 60)
        logger.info("Tracking läuft...")
        if not config.HEADLESS_MODE:
            logger.info("  q = Beenden")
            logger.info("  Space = Pause/Resume")
            logger.info("  r = Tracker zurücksetzen")
            logger.info("  f = Vollbild-Toggle")
        else:
            logger.info("  Ctrl+C = Beenden")
        logger.info("=" * 60)
        
        paused = False
        frame_count = 0
        total_detections = 0
        tracked_frames = 0
        
        # Haupt-Loop
        while True:
            if not paused:
                # Frame lesen
                success, frame = video_capture.read()
                
                if not success:
                    logger.warning("Frame konnte nicht gelesen werden - Stream beendet")
                    break
                
                frame_count += 1
                
                # Performance-Management: Frame skippen wenn nötig
                if perf_manager:
                    if not perf_manager.should_process_frame():
                        # Frame überspringen
                        continue
                    perf_manager.update_frame_time()
                
                # Person Detection
                detections = detector.detect(frame)
                total_detections += len(detections)
                
                # Tracking aktualisieren
                tracked_detection = tracker.update(detections, frame.shape)
                
                if tracked_detection:
                    tracked_frames += 1
                
                # PTZ-Controller updaten (wenn aktiviert)
                if config.ENABLE_PTZ and ptz_controller:
                    ptz_controller.update(
                        tracked_detection,
                        frame.shape[1],  # width
                        frame.shape[0]   # height
                    )
                
                # Visualisierung (wenn nicht headless)
                if not config.HEADLESS_MODE and visualizer:
                    key = visualizer.show(frame, tracked_detection, ptz_controller)
                    
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
                    elif key == ord('f'):
                        # Vollbild-Toggle
                        import cv2
                        current = cv2.getWindowProperty(
                            visualizer.window_name,
                            cv2.WND_PROP_FULLSCREEN
                        )
                        new_mode = cv2.WINDOW_NORMAL if current == cv2.WINDOW_FULLSCREEN else cv2.WINDOW_FULLSCREEN
                        cv2.setWindowProperty(
                            visualizer.window_name,
                            cv2.WND_PROP_FULLSCREEN,
                            new_mode
                        )
                
                # Headless-Modus: nur Logging
                if config.HEADLESS_MODE and frame_count % 100 == 0:
                    logger.info(f"Frame {frame_count}: {len(detections)} Detections, Tracking: {tracked_detection is not None}")
            
            else:
                # Pause-Modus
                if visualizer:
                    import cv2
                    key = cv2.waitKey(100) & 0xFF
                    if key == ord('q'):
                        logger.info("\nBeenden durch Benutzer...")
                        break
                    elif key == ord(' '):
                        paused = False
                        logger.info("Stream fortgesetzt")
    
    except KeyboardInterrupt:
        logger.info("\nAnwendung durch Benutzer beendet")
    
    except Exception as e:
        logger.exception(f"Fehler in Hauptschleife: {e}")
        return 1
    
    finally:
        # Aufräumen
        logger.info("\nSchließe Anwendung...")
        
        # PTZ-Ressourcen bereinigen
        if ptz_rest_server:
            logger.info("Stoppe PTZ REST-Server...")
            ptz_rest_server.stop()
        
        if ptz_controller:
            logger.info("PTZ-Controller bereinigt")
        
        if threaded_capture:
            threaded_capture.stop()
        elif video_source:
            video_source.release()
        
        if visualizer:
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
        if visualizer:
            logger.info(f"  Durchschnitt FPS: {visualizer.fps_counter.get_average_fps():.1f}")
            logger.info(f"  Laufzeit: {visualizer.fps_counter.get_elapsed_time():.1f}s")
        
        # Performance-Manager Statistiken
        if perf_manager:
            perf_stats = perf_manager.get_statistics()
            logger.info(f"\nPerformance-Optimierung:")
            logger.info(f"  Verarbeitete Frames: {perf_stats['processed_frames']}/{perf_stats['total_frames']}")
            logger.info(f"  Übersprungene Frames: {perf_stats['skipped_frames']} ({perf_stats['skip_rate']:.1f}%)")
            logger.info(f"  Processing FPS: {perf_stats['current_fps']:.1f}")
        
        logger.info("=" * 60)
        logger.info("PTZ Tracking beendet")
        logger.info("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
