"""
Basis-Tests für PTZ Tracking
"""

import pytest
import numpy as np
from pathlib import Path


def test_imports():
    """Test dass alle Module importierbar sind"""
    try:
        from src import config
        from src.utils import logger, performance
        from src.stream import video_source, ffmpeg_handler
        from src.tracking import person_detector, tracker
        from src.display import visualizer
        assert True
    except ImportError as e:
        pytest.fail(f"Import-Fehler: {e}")


def test_config_validation():
    """Test Konfigurationsvalidierung"""
    from src import config
    
    assert config.VIDEO_SOURCE in ["ffmpeg", "webcam", "file"]
    assert config.RESOLUTION[0] > 0
    assert config.RESOLUTION[1] > 0
    assert 0 < config.CONFIDENCE_THRESHOLD <= 1.0


def test_fps_counter():
    """Test FPS-Counter"""
    from src.utils.performance import FPSCounter
    import time
    
    fps = FPSCounter()
    
    for _ in range(10):
        fps.update()
        time.sleep(0.01)
    
    assert fps.get_frame_count() == 10
    assert fps.get_fps() > 0


def test_detection_class():
    """Test Detection-Klasse"""
    from src.tracking.person_detector import Detection
    
    det = Detection(bbox=(100, 100, 300, 400), confidence=0.9)
    
    assert det.x1 == 100
    assert det.y1 == 100
    assert det.x2 == 300
    assert det.y2 == 400
    assert det.width == 200
    assert det.height == 300
    assert det.area == 60000
    assert det.center == (200, 250)


def test_logger_setup():
    """Test Logger-Setup"""
    from src.utils.logger import setup_logger
    
    logger = setup_logger("test_logger")
    assert logger is not None
    
    # Test verschiedene Log-Levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")


if __name__ == "__main__":
    # Tests manuell ausführen
    print("Running tests...")
    
    test_imports()
    print("✓ Import test passed")
    
    test_config_validation()
    print("✓ Config test passed")
    
    test_fps_counter()
    print("✓ FPS counter test passed")
    
    test_detection_class()
    print("✓ Detection class test passed")
    
    test_logger_setup()
    print("✓ Logger test passed")
    
    print("\nAll tests passed!")
