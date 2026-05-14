"""
Threaded Video Capture
Liest Frames im Hintergrund-Thread für bessere Performance
"""

import threading
import queue
from typing import Optional, Tuple
import numpy as np

from src.utils.logger import get_logger
from src.stream.video_source import VideoSource


logger = get_logger(__name__)


class ThreadedVideoCapture:
    """
    Wrapper für VideoSource mit Threading für asynchrones Frame-Lesen
    """
    
    def __init__(
        self,
        video_source: VideoSource,
        buffer_size: int = 2
    ):
        """
        Args:
            video_source: VideoSource-Instanz (WebcamHandler, etc.)
            buffer_size: Größe des Frame-Buffers (größer = mehr Latenz, aber stabiler)
        """
        self.video_source = video_source
        self.buffer_size = buffer_size
        
        # Frame Queue
        self.frame_queue = queue.Queue(maxsize=buffer_size)
        
        # Threading
        self.thread = None
        self.stopped = False
        self.lock = threading.Lock()
        
        # Statistiken
        self.frames_read = 0
        self.frames_dropped = 0
        
        logger.info(f"ThreadedVideoCapture initialisiert (Buffer: {buffer_size})")
    
    def start(self) -> bool:
        """
        Startet Video-Quelle und Background-Thread
        
        Returns:
            True wenn erfolgreich
        """
        # Video-Quelle öffnen
        if not self.video_source.open():
            logger.error("Video-Quelle konnte nicht geöffnet werden")
            return False
        
        # Thread starten
        self.stopped = False
        self.thread = threading.Thread(target=self._reader_thread, daemon=True)
        self.thread.start()
        
        logger.info("✓ ThreadedVideoCapture gestartet")
        return True
    
    def _reader_thread(self):
        """
        Background-Thread der kontinuierlich Frames liest
        """
        logger.debug("Reader-Thread gestartet")
        
        while not self.stopped:
            # Frame lesen
            success, frame = self.video_source.read()
            
            if not success:
                logger.warning("Frame-Lesen fehlgeschlagen")
                self.stopped = True
                break
            
            self.frames_read += 1
            
            # Frame in Queue legen
            try:
                # Bei vollem Buffer: ältesten Frame verwerfen
                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()
                        self.frames_dropped += 1
                    except queue.Empty:
                        pass
                
                self.frame_queue.put(frame, block=False)
                
            except queue.Full:
                # Sollte nicht passieren durch obige Logik
                self.frames_dropped += 1
        
        logger.debug("Reader-Thread beendet")
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Liest neuesten Frame aus Queue
        
        Returns:
            (success, frame)
        """
        try:
            # Timeout um nicht ewig zu blocken
            frame = self.frame_queue.get(timeout=1.0)
            return True, frame
            
        except queue.Empty:
            return False, None
    
    def stop(self):
        """
        Stoppt Thread und schließt Video-Quelle
        """
        logger.info("Stoppe ThreadedVideoCapture...")
        
        # Thread stoppen
        self.stopped = True
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        # Video-Quelle schließen
        self.video_source.release()
        
        # Statistiken
        if self.frames_dropped > 0:
            drop_rate = (self.frames_dropped / self.frames_read * 100) if self.frames_read > 0 else 0
            logger.info(f"Frames gelesen: {self.frames_read}, verworfen: {self.frames_dropped} ({drop_rate:.1f}%)")
        
        logger.info("✓ ThreadedVideoCapture gestoppt")
    
    def get_resolution(self) -> Tuple[int, int]:
        """Returns: (width, height)"""
        return self.video_source.get_resolution()
    
    def get_fps(self) -> float:
        """Returns: FPS"""
        return self.video_source.get_fps()
    
    def __enter__(self):
        """Context Manager Support"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager Support"""
        self.stop()
        return False


if __name__ == "__main__":
    # Test
    import time
    import cv2
    
    from src.stream import create_video_source
    
    logger.info("=" * 60)
    logger.info("Testing ThreadedVideoCapture...")
    logger.info("=" * 60)
    
    # Webcam-Source erstellen
    logger.info("\n1. Erstelle Webcam-Source...")
    video_source = create_video_source("webcam", camera_index=0)
    
    # ThreadedVideoCapture erstellen
    logger.info("\n2. Erstelle ThreadedVideoCapture...")
    threaded_capture = ThreadedVideoCapture(video_source, buffer_size=2)
    
    # Starten
    logger.info("\n3. Starte Capture...")
    if not threaded_capture.start():
        logger.error("Start fehlgeschlagen")
        exit(1)
    
    # Test-Window
    cv2.namedWindow("ThreadedCapture Test", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("ThreadedCapture Test", 640, 480)
    
    logger.info("\n4. Lese Frames (10 Sekunden)...")
    logger.info("   Drücke 'q' zum vorzeitigen Beenden")
    
    start_time = time.time()
    frame_count = 0
    
    try:
        while time.time() - start_time < 10.0:
            success, frame = threaded_capture.read()
            
            if success:
                frame_count += 1
                
                # Info auf Frame
                cv2.putText(
                    frame,
                    f"Frame: {frame_count}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 255, 0),
                    2
                )
                
                cv2.imshow("ThreadedCapture Test", frame)
                
                # Key-Events
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    
    except KeyboardInterrupt:
        logger.info("\nBeenden durch Ctrl+C...")
    
    finally:
        # Stoppen
        logger.info("\n5. Stoppe Capture...")
        threaded_capture.stop()
        cv2.destroyAllWindows()
        
        # Statistiken
        elapsed = time.time() - start_time
        fps = frame_count / elapsed if elapsed > 0 else 0
        
        logger.info("\n" + "=" * 60)
        logger.info("Test abgeschlossen:")
        logger.info(f"  Frames: {frame_count}")
        logger.info(f"  Zeit: {elapsed:.1f}s")
        logger.info(f"  FPS: {fps:.1f}")
        logger.info("=" * 60)
