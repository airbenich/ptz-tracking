"""
Stream-Handler für Video-Input
"""

from src.stream.video_source import VideoSource
from src.stream.webcam_handler import WebcamHandler
from src.stream.video_file_handler import VideoFileHandler
from src.stream.ffmpeg_handler import FFmpegStreamHandler
from src.stream.stream_factory import create_video_source
from src.stream.threaded_capture import ThreadedVideoCapture

__all__ = [
    'VideoSource',
    'WebcamHandler',
    'VideoFileHandler',
    'FFmpegStreamHandler',
    'create_video_source',
    'ThreadedVideoCapture',
]
