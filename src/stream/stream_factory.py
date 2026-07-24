"""
Stream Factory
Erstellt den passenden Video-Handler basierend auf Konfiguration
"""

from typing import Optional

from src.utils.logger import get_logger
from src import config
from src.stream.video_source import VideoSource
from src.stream.webcam_handler import WebcamHandler
from src.stream.video_file_handler import VideoFileHandler
from src.stream.ffmpeg_handler import FFmpegStreamHandler

# GStreamer Handler (optional - falls installiert)
try:
    from src.stream.gstreamer_handler import GStreamerHandler, GST_AVAILABLE
    GSTREAMER_ENABLED = GST_AVAILABLE
except ImportError:
    GSTREAMER_ENABLED = False
    GStreamerHandler = None


logger = get_logger(__name__)


def create_video_source(
    source_type: Optional[str] = None,
    **kwargs
) -> VideoSource:
    """
    Factory-Funktion zum Erstellen der passenden Video-Quelle
    
    Args:
        source_type: "gstreamer", "webcam", "file", "ffmpeg" (oder None für config.VIDEO_SOURCE)
        **kwargs: Zusätzliche Parameter für den Handler
    
    Returns:
        VideoSource-Instanz
    
    Raises:
        ValueError: Wenn source_type ungültig ist
    """
    source_type = source_type or config.VIDEO_SOURCE
    
    logger.info(f"Erstelle Video-Quelle: {source_type}")
    
    if source_type == "gstreamer":
        # GStreamer-Handler (EMPFOHLEN)
        if not GSTREAMER_ENABLED:
            logger.error("GStreamer ist nicht verfügbar!")
            logger.error("Installation: macOS: brew install gstreamer gst-python gst-plugins-base gst-plugins-good gst-plugins-bad")
            logger.error("Installation: Linux: apt-get install python3-gi gstreamer1.0-tools gstreamer1.0-plugins-*")
            logger.warning("Fallback auf FFmpeg...")
            source_type = "ffmpeg"
        else:
            device = kwargs.get('device') or config.GSTREAMER_INPUT_DEVICE
            device_number = config.GSTREAMER_DEVICE_NUMBERS.get(device, 0)
            
            return GStreamerHandler(
                device=device,
                resolution=kwargs.get('resolution', config.RESOLUTION),
                fps=kwargs.get('fps', config.FPS_TARGET),
                device_number=device_number,
                connection=kwargs.get('connection', config.DECKLINK_CONNECTION)
            )
    
    if source_type == "webcam":
        # Webcam-Handler
        camera_index = kwargs.get('camera_index', 0)
        return WebcamHandler(
            camera_index=camera_index,
            resolution=kwargs.get('resolution'),
            fps=kwargs.get('fps')
        )
    
    elif source_type == "file":
        # Video-File-Handler
        file_path = kwargs.get('file_path') or config.VIDEO_FILE_PATH
        
        if not file_path:
            raise ValueError("file_path muss für source_type='file' angegeben werden")
        
        return VideoFileHandler(
            file_path=file_path,
            loop=kwargs.get('loop', True)
        )
    
    elif source_type == "ffmpeg":
        # FFmpeg-Handler (Legacy - Fallback)
        return FFmpegStreamHandler(
            device=kwargs.get('device'),
            resolution=kwargs.get('resolution'),
            fps=kwargs.get('fps')
        )
    
    else:
        raise ValueError(f"Ungültiger source_type: {source_type}. Erlaubt: gstreamer, webcam, file, ffmpeg")


if __name__ == "__main__":
    # Test
    logger.info("Testing Stream Factory...")
    logger.info("=" * 60)
    
    # Test 0: GStreamer-Handler (EMPFOHLEN)
    logger.info("\n0. GStreamer-Handler erstellen:")
    if GSTREAMER_ENABLED:
        try:
            gstreamer = create_video_source("gstreamer", device="Blackmagic")
            logger.info(f"✓ Erstellt: {gstreamer.__class__.__name__}")
        except Exception as e:
            logger.error(f"✗ Fehler: {e}")
    else:
        logger.warning("✗ GStreamer nicht verfügbar")
    
    # Test 1: Webcam
    logger.info("\n1. Webcam-Handler erstellen:")
    try:
        webcam = create_video_source("webcam", camera_index=0)
        logger.info(f"✓ Erstellt: {webcam.__class__.__name__}")
    except Exception as e:
        logger.error(f"✗ Fehler: {e}")
    
    # Test 2: File (ohne echte Datei)
    logger.info("\n2. File-Handler erstellen:")
    try:
        file_handler = create_video_source("file", file_path="test.mp4")
        logger.info(f"✓ Erstellt: {file_handler.__class__.__name__}")
    except Exception as e:
        logger.error(f"✗ Fehler: {e}")
    
    # Test 3: FFmpeg (Legacy)
    logger.info("\n3. FFmpeg-Handler erstellen:")
    try:
        ffmpeg = create_video_source("ffmpeg")
        logger.info(f"✓ Erstellt: {ffmpeg.__class__.__name__}")
    except Exception as e:
        logger.error(f"✗ Fehler: {e}")

    
    # Test 4: Aus Config
    logger.info(f"\n4. Handler aus Config erstellen (VIDEO_SOURCE={config.VIDEO_SOURCE}):")
    try:
        default = create_video_source()
        logger.info(f"✓ Erstellt: {default.__class__.__name__}")
    except Exception as e:
        logger.error(f"✗ Fehler: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ Factory-Tests abgeschlossen")
