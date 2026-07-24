"""
Konfigurationsverwaltung für PTZ Tracking
Alle Einstellungen für Video-Input, Tracking und Display
"""

import os
from pathlib import Path

# ============================================================================
# Projekt-Pfade
# ============================================================================

# Basis-Verzeichnis des Projekts
BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"
OUTPUT_DIR = BASE_DIR / "output"

# Verzeichnisse erstellen falls nicht vorhanden
LOGS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================================
# Video-Input Konfiguration
# ============================================================================

# Video-Quelle: "gstreamer", "ffmpeg", "webcam", "file"
# EMPFOHLEN: "gstreamer" für bessere Performance und niedrigere Latenz
VIDEO_SOURCE = "gstreamer"

# GStreamer Input-Device: "Blackmagic", "Elgato", "Webcam"
GSTREAMER_INPUT_DEVICE = "Blackmagic"

# ffmpeg Input-Device: "Blackmagic", "Elgato", "Webcam" (Legacy)
FFMPEG_INPUT_DEVICE = "Blackmagic"

# Video-Auflösung (Input)
RESOLUTION = (1920, 1080)  # Full HD

# Ziel-Framerate (WICHTIG: Muss mit PTZ-Kamera übereinstimmen - 30 oder 50 FPS)
# Prüfen Sie: PTZ-Kamera Menü → System → Video Format → 1080p50 oder 1080p30
# HINWEIS: Bei 50 FPS wird auf 25 FPS reduziert (ffmpeg -r 25 Flag)
FPS_TARGET = 50  # PTZ-Kamera sendet 50 FPS, ffmpeg reduziert auf 25 FPS

# Spezifische ffmpeg-Device-Namen (für macOS mit avfoundation)
# macOS: Verwende Device-Index (z.B. "1" für Video-Device [1])
# Linux: Verwende Device-Nummer (z.B. "0" für /dev/video0)
# Windows: Verwende Device-Namen
# HINWEIS: Elgato wird automatisch erkannt (sucht nach "Cam Link 4K")
FFMPEG_DEVICE_NAMES = {
    "Blackmagic": "Blackmagic",  # Kann je nach System variieren
    "Elgato": "0",  # Fallback-Wert, wird automatisch erkannt bei jedem Start
    "Webcam": "0",  # Standard Webcam Index
}

# ffmpeg-Kommando-Template (wird in ffmpeg_handler.py verwendet)
# Für Linux: "-f v4l2" statt "-f avfoundation"
FFMPEG_INPUT_FORMAT = "avfoundation"  # macOS: avfoundation, Linux: v4l2

# Video-Datei Pfad (wenn VIDEO_SOURCE = "file")
VIDEO_FILE_PATH = ""

# ============================================================================
# GStreamer Konfiguration (EMPFOHLEN für beste Performance)
# ============================================================================

# GStreamer Device-Nummern
# Blackmagic DeckLink: 0, 1, 2, ... (für mehrere Cards)
# V4L2 Linux: 0 = /dev/video0, 1 = /dev/video1, ...
# AVFoundation macOS: 0, 1, 2, ... (automatisch erkannt)
GSTREAMER_DEVICE_NUMBERS = {
    "Blackmagic": 0,  # DeckLink Device-Nummer
    "Elgato": 0,      # V4L2/AVFoundation Device-Index
    "Webcam": 0,      # Standard Webcam Index
}

# DeckLink Verbindungstyp (nur für Blackmagic)
# Optionen: "sdi", "hdmi", "optical-sdi", "component", "composite", "s-video"
DECKLINK_CONNECTION = "sdi"

# DeckLink Video-Modus (nur für Blackmagic)
# Format: [resolution][progressive/interlaced][framerate]
# Beispiele: "1080p25", "1080p50", "1080i50", "2160p30", "720p50"
# WICHTIG: Muss mit FPS_TARGET übereinstimmen!
DECKLINK_MODE = "1080p25"  # 1080p @ 25 FPS

# GStreamer Buffer-Einstellungen
# max-buffers: Maximale Anzahl gepufferter Frames (2 = niedrige Latenz)
# drop: Alte Frames verwerfen wenn Buffer voll (true = Echtzeit-Priorität)
GSTREAMER_MAX_BUFFERS = 2
GSTREAMER_DROP_OLD_BUFFERS = True

# Latenz-Kontrolle (Millisekunden)
# Niedrigere Werte = bessere Reaktionszeit für PTZ-Tracking
GSTREAMER_BUFFER_LATENCY = 0  # 0 = minimale Latenz

# Hardware-Beschleunigung (GPU)
# Automatische Auswahl der besten verfügbaren Methode
GSTREAMER_HW_ACCELERATION = True

# ============================================================================
# FFmpeg Konfiguration (Legacy - für Fallback)
# ============================================================================

# YOLO-Modell: "yolov8n.pt", "yolov8s.pt", "yolov8m.pt", "yolov8l.pt", "yolov8x.pt"
# n = nano (schnellste), x = extra large (genaueste)
MODEL = "yolov8n.pt"

# Konfidenz-Schwellwert für Detections (0.0 - 1.0)
CONFIDENCE_THRESHOLD = 0.5

# Person-Klasse ID im COCO-Dataset
PERSON_CLASS_ID = 0

# GPU-Beschleunigung aktivieren (CUDA)
GPU_ENABLED = True

# Device für YOLO (wird automatisch gesetzt basierend auf GPU_ENABLED)
# "cuda:0" für NVIDIA GPU, "mps" für Apple Silicon, "cpu" für CPU
DEVICE = None  # None = automatische Auswahl

# ============================================================================
# Pose-Estimation Konfiguration
# ============================================================================

# Pose-Estimation aktivieren
ENABLE_POSE_ESTIMATION = True

# Pose-Modell: "yolov8n-pose.pt", "yolov8s-pose.pt", "yolov8m-pose.pt", etc.
POSE_MODEL = "yolov8n-pose.pt"

# Keypoints anzeigen (Gelenke, Körperteile)
SHOW_KEYPOINTS = False

# Face-Keypoints anzeigen (Nase, Augen, Ohren - Keypoints 0-4)
SHOW_FACE_KEYPOINTS = True

# Skeleton anzeigen (Linien zwischen Keypoints)
SHOW_SKELETON = False

# Keypoint-Farbe (BGR)
KEYPOINT_COLOR = (255, 255, 255)  # Weiß

# Keypoint-Radius (Pixel)
KEYPOINT_RADIUS = 10

# Skeleton-Farbe (BGR)
SKELETON_COLOR = (255, 255, 255)  # Weiß

# Skeleton-Dicke (Pixel)
SKELETON_THICKNESS = 2

# Konfidenz-Schwellwert für Keypoints (0.0 - 1.0)
KEYPOINT_CONFIDENCE_THRESHOLD = 0.3

# Transparenz für Skeleton und Keypoints (0.0 - 1.0)
# 0.0 = komplett transparent, 1.0 = komplett opak
POSE_OPACITY = 0.75  # 75% Opacity

# ============================================================================
# PTZ-Kamera Steuerung (Panasonic AW-HE130)
# ============================================================================

# PTZ-Steuerung aktivieren
ENABLE_PTZ = True

# Kamera IP-Adresse
PTZ_CAMERA_IP = "10.1.3.43"

# Kamera HTTP-Port
PTZ_CAMERA_PORT = 80

# Kamera Benutzer/Passwort (falls erforderlich)
PTZ_CAMERA_USER = ""
PTZ_CAMERA_PASSWORD = ""

# Zielposition: Person horizontal zentriert
PTZ_TARGET_X = 0.5  # 0.0 = links, 1.0 = rechts, 0.5 = Mitte

# Headroom: Abstand zwischen BBox-Oberkante und oberem Bildrand (0.0-1.0)
# Broadcast-Standard: 10-15% des Frame-Heights als "Luftabstand" über Kopf
PTZ_HEADROOM = 0.12  # 12% des Frames als Abstand über der Person

# Dead-Zone: Bereich um Zielposition wo nicht korrigiert wird (0.0-1.0)
PTZ_DEADZONE_X = 0.02  # ±2% horizontal (engere Dead-Zone für präziseres Tracking)
PTZ_DEADZONE_Y = 0.02  # ±2% vertikal

# Speed-basierte Steuerung (PTS-Befehle)
# Speed-Range: 01-99, wobei 50=Stop, <50=links/unten, >50=rechts/oben
PTZ_MAX_SPEED = 80      # Maximale Geschwindigkeit (bei großer Distanz)
PTZ_MAX_PAN_SPEED = 20  # Maximale Pan-Geschwindigkeit (sanftere horizontale Bewegung, ±25 von Stop=50)
PTZ_MAX_TILT_SPEED = 20 # Maximale Tilt-Geschwindigkeit (sanftere vertikale Bewegung, ±25 von Stop=50)
PTZ_MIN_SPEED = 5       # Minimale Geschwindigkeit (nahe am Ziel)
PTZ_SPEED_RAMP = 0   # Speed-Ramping-Faktor (0.0-1.0, höher=progressiver) - 0 = linear, schneller

# Smoothing-Faktor für Speed-Änderungen (0.0-1.0)
# Verhindert abrupte Geschwindigkeitswechsel für broadcast-quality
PTZ_SPEED_SMOOTHING = 0.3  # 30% neue Speed, 70% alte Speed

# Minimale Bewegungsschwelle (Pan/Tilt Units)
# Kleinere Bewegungen werden ignoriert für stabileres Bild
PTZ_MIN_MOVEMENT = 10

# Update-Rate (Sekunden zwischen PTZ-Updates)
# Panasonic HE130: Minimal 130ms zwischen Befehlen laut Spec
PTZ_UPDATE_INTERVAL = 0.13  # 130ms Mindest-Delay

# PTZ Speed-Neutral (50 = Stop)
PTZ_SPEED_STOP = 50

# REST-API für PTZ-Steuerung
PTZ_REST_ENABLED = True
PTZ_REST_HOST = "0.0.0.0"  # Alle Interfaces
PTZ_REST_PORT = 8090

# PTZ initial aktiviert
PTZ_ENABLED_ON_START = False  # Startet deaktiviert, muss über REST aktiviert werden

# ============================================================================
# Bitfocus Companion Integration
# ============================================================================

# Companion Custom Variables aktivieren
COMPANION_ENABLED = True

# Companion Server URL
COMPANION_HOST = "10.1.1.30"
COMPANION_PORT = 8000
COMPANION_BASE_URL = f"http://{COMPANION_HOST}:{COMPANION_PORT}"

# Timeout für Companion-Requests (Sekunden)
COMPANION_TIMEOUT = 2.0

# ============================================================================
# Tracking-Konfiguration
# ============================================================================

# Tracking-Methode: "largest_bbox", "most_centered", "highest_confidence"
TRACKING_METHOD = "largest_bbox"

# Smoothing für stabileres Tracking
SMOOTHING_ENABLED = True
SMOOTHING_FACTOR = 0.7  # 0.0 = kein Smoothing, 1.0 = maximales Smoothing

# Maximale Frames ohne Detection bevor Tracking zurückgesetzt wird
MAX_FRAMES_WITHOUT_DETECTION = 90  # ~3 Sekunden bei 30 FPS - verhindert ID-Verlust bei kurzen Ausfällen

# ============================================================================
# Multi-Person-Tracking Konfiguration
# ============================================================================

# Multi-Person-Tracking aktivieren (trackt alle Personen mit IDs)
ENABLE_MULTI_PERSON_TRACKING = True

# Maximale Distanz für Track-Zuordnung (Pixel)
# Detections mit größerer Distanz werden als neue Person erkannt
MULTI_PERSON_MAX_DISTANCE = 200  # Erhöht für bessere Zuordnung bei Bewegung

# Minimale konsekutive Detections bevor neue Track-ID vergeben wird
# Verhindert "Flackern" durch kurzzeitige Fehl-Detections
MIN_CONSECUTIVE_DETECTIONS = 3  # Neue Person muss 3 Frames lang erkannt werden

# Alle Personen mit IDs anzeigen (nicht nur aktive)
SHOW_ALL_TRACKED_PERSONS = True

# Farbe für inaktive Personen (BGR)
INACTIVE_PERSON_COLOR = (100, 100, 100)  # Grau

# Farbe für aktive Person (BGR)
ACTIVE_PERSON_COLOR = (255, 255, 255)  # Grün

# ============================================================================
# Display-Konfiguration
# ============================================================================

# Display-Auflösung (kann kleiner als Input sein für Performance)
DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 720

# Bounding-Box anzeigen
SHOW_BBOX = False

# Bounding-Box Farbe (BGR Format)
BBOX_COLOR = (255, 255, 255)  # Weiß

# Bounding-Box Dicke (Pixel)
BBOX_THICKNESS = 2

# Text-Farbe für Info-Overlay (BGR)
TEXT_COLOR = (255, 255, 255)  # Weiß

# Text-Größe
TEXT_SCALE = 1
TEXT_THICKNESS = 2

# FPS-Counter anzeigen
SHOW_FPS = True

# Tracking-Informationen anzeigen (Position, Größe, etc.)
SHOW_INFO = True

# Headroom-Guide-Linie anzeigen (zeigt Zielposition für PTZ-Steuerung)
SHOW_HEADROOM_LINE = True
SHOW_HEADROOM_LINE_DEADZONE = False
SHOW_HEADROOM_LINE_ON_PERSON = False

# Vollbild-Modus
FULLSCREEN = False

# Window-Name
WINDOW_NAME = "PTZ Tracking"

# ============================================================================
# Performance-Optimierung
# ============================================================================

# Threading für Video-Input aktivieren
THREADED_CAPTURE = True

# Buffer-Größe für threaded capture (Frames)
CAPTURE_BUFFER_SIZE = 2

# Frame-Skipping bei schlechter Performance aktivieren
ENABLE_FRAME_SKIP = True

# Performance-Schwellwert für Frame-Skip (0.0-1.0)
# Bei Performance < threshold * target_fps wird geskippt
FRAME_SKIP_THRESHOLD = 0.7

# Maximale Skip-Rate (0 = kein Skip, 1 = jeden 2., 2 = jeden 3., etc.)
MAX_SKIP_RATE = 3

# ============================================================================
# Application Mode
# ============================================================================

# Als Service/Daemon laufen
RUN_AS_SERVICE = False

# Headless-Modus (ohne Display, nur Tracking-Daten)
HEADLESS_MODE = False

# Automatischer Neustart bei Stream-Fehler
AUTO_RESTART = True

# Maximale Neustart-Versuche
MAX_RESTART_ATTEMPTS = 5

# Wartezeit zwischen Neustarts (Sekunden)
RESTART_DELAY = 3

# ============================================================================
# Logging-Konfiguration
# ============================================================================

# Log-Level: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
LOG_LEVEL = "INFO"

# Logging in Console
LOG_TO_CONSOLE = True

# Logging in Datei
LOG_TO_FILE = False

# Log-Datei Pfad
LOG_FILE = LOGS_DIR / "ptz_tracking.log"

# Log-Format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Zeitformat für Logs
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ============================================================================
# Performance-Konfiguration
# ============================================================================

# Frame-Buffer-Größe
FRAME_BUFFER_SIZE = 2

# Threading aktivieren
USE_THREADING = True

# Anzahl Worker-Threads
NUM_THREADS = 2

# Frame-Skipping bei niedriger Performance
ENABLE_FRAME_SKIP = False

# Maximale Frame-Skip-Rate (z.B. 2 = jeder 2. Frame)
MAX_FRAME_SKIP = 2

# ============================================================================
# Entwickler-Optionen
# ============================================================================

# Debug-Modus (zusätzliche Ausgaben)
DEBUG_MODE = False

# Performance-Profiling
ENABLE_PROFILING = False

# Screenshots speichern (bei 's'-Taste)
ENABLE_SCREENSHOTS = True

# Screenshot-Verzeichnis
SCREENSHOT_DIR = OUTPUT_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)


# ============================================================================
# Konfiguration validieren und anpassen
# ============================================================================

def validate_config():
    """Validiert die Konfiguration und passt sie bei Bedarf an"""
    global DEVICE, FFMPEG_INPUT_DEVICE
    
    # Device automatisch setzen
    if DEVICE is None:
        if GPU_ENABLED:
            import torch
            if torch.cuda.is_available():
                DEVICE = "cuda:0"
            elif torch.backends.mps.is_available():
                DEVICE = "mps"
            else:
                DEVICE = "cpu"
                print("⚠️  GPU aktiviert, aber keine GPU verfügbar. Verwende CPU.")
        else:
            DEVICE = "cpu"
    
    # Modell-Pfad prüfen
    model_path = MODELS_DIR / MODEL
    if not model_path.exists():
        print(f"ℹ️  YOLO-Modell {MODEL} wird beim ersten Start heruntergeladen.")
    
    # Video-Source validieren
    if VIDEO_SOURCE not in ["ffmpeg", "webcam", "file"]:
        raise ValueError(f"Ungültige VIDEO_SOURCE: {VIDEO_SOURCE}")
    
    # Bei file-Quelle: Pfad prüfen
    if VIDEO_SOURCE == "file" and not VIDEO_FILE_PATH:
        raise ValueError("VIDEO_FILE_PATH muss gesetzt sein wenn VIDEO_SOURCE='file'")
    
    print(f"✓ Konfiguration validiert. Device: {DEVICE}")


# Beim Import automatisch validieren
if __name__ != "__main__":
    validate_config()


if __name__ == "__main__":
    # Konfiguration ausgeben
    print("=" * 60)
    print("PTZ Tracking - Konfiguration")
    print("=" * 60)
    print(f"\nVideo-Input:")
    print(f"  Source: {VIDEO_SOURCE}")
    print(f"  Device: {FFMPEG_INPUT_DEVICE}")
    print(f"  Resolution: {RESOLUTION[0]}x{RESOLUTION[1]}")
    print(f"  FPS Target: {FPS_TARGET}")
    print(f"\nTracking:")
    print(f"  Model: {MODEL}")
    print(f"  Device: {DEVICE}")
    print(f"  Confidence: {CONFIDENCE_THRESHOLD}")
    print(f"  Method: {TRACKING_METHOD}")
    print(f"\nDisplay:")
    print(f"  Size: {DISPLAY_WIDTH}x{DISPLAY_HEIGHT}")
    print(f"  Show FPS: {SHOW_FPS}")
    print(f"  Show Info: {SHOW_INFO}")
    print(f"\nApplication:")
    print(f"  Service Mode: {RUN_AS_SERVICE}")
    print(f"  Headless: {HEADLESS_MODE}")
    print(f"  Auto Restart: {AUTO_RESTART}")
    print(f"\nLogging:")
    print(f"  Level: {LOG_LEVEL}")
    print(f"  Console: {LOG_TO_CONSOLE}")
    print(f"  File: {LOG_TO_FILE}")
    print("=" * 60)
