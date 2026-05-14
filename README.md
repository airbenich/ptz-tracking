# PTZ Tracking

Echtzeit-Tracking von Personen in Videostreams mit Python, OpenCV und YOLOv8.

## Features

### ✅ Vollständig implementiert

- 🎥 **Video-Input-Handler**
  - FFmpeg-Integration für professionelle Hardware (Blackmagic DeckLink, Elgato Cam Link)
  - Webcam-Support für Development/Testing
  - Video-Datei-Wiedergabe mit Loop-Option
  - Plattform-übergreifend (macOS/Linux/Windows)

- 👤 **Person Detection**
  - YOLOv8-basierte Echtzeit-Erkennung
  - Automatische Person-Filterung (COCO class_id=0)
  - Konfigurierbare Confidence-Schwellwerte
  - GPU-Beschleunigung (CUDA/MPS/CPU)

- 📍 **Tracking**
  - Frame-to-Frame Tracking der prominentesten Person
  - Drei Tracking-Methoden:
    - `largest_bbox` - Größte Person
    - `most_centered` - Am nächsten zur Bildmitte
    - `highest_confidence` - Höchste Erkennungssicherheit
  - Smoothing-Algorithmus für stabile Bounding Boxes
  - Automatische Tracking-Loss-Behandlung

- 🖥️ **Visualisierung**
  - OpenCV-basierte Live-Anzeige
  - Bounding Box mit Confidence-Score
  - **Pose-Estimation & Skeleton-Overlay** 🦴
    - 17 COCO-Keypoints (Gelenke, Körperteile)
    - Skeleton-Linien zwischen Keypoints
    - Konfigurierbare Farben und Sichtbarkeit
    - Konfidenz-basierte Filterung
  - **PTZ-Status-Anzeige** 🎯
    - PTZ ON/OFF Indicator (grün/rot)
  - FPS-Counter und Performance-Monitoring
  - Info-Overlay (Position, Größe, Area)
  - Vollbild-Modus
  - Interaktive Keyboard-Steuerung

- 🎯 **PTZ-Kamera-Steuerung** ⭐ NEU
  - Automatische Pan/Tilt-Steuerung für Panasonic AW-HE130
  - Person horizontal zentriert halten
  - Vertikale Positionierung nach goldenem Schnitt
  - Smooth, einstellbare Bewegungen (Smoothing-Faktor 0-1)
  - Dead-Zone zur Vermeidung von Mikrobewegungen
  - REST-API für Ein-/Ausschaltung (HTTP GET)
  - Status-Anzeige im Visualizer
  - Kein automatischer Zoom (Operator-Kontrolle)

- ⚡ **Performance**
  - Optimiert für >15 FPS
  - Apple Silicon MPS-Support
  - NVIDIA CUDA-Support
  - Automatische Device-Detection

- 🔧 **Flexibilität**
  - Umfassende CLI-Argumente
  - Headless-Modus für Server-Betrieb
  - Modulare Architektur
  - Einfach erweiterbar

- 🚀 **Performance-Optimierung** ⚡
  - Threading für asynchrones Frame-Lesen (+57% schneller!)
  - Intelligentes Frame-Skipping bei hoher Last
  - Adaptive Performance-Anpassung
  - Konfigurierbarer Frame-Buffer
  - Erreicht 27.7 FPS (Ziel: >15 FPS) ✅

- 🔧 **Service/Daemon-Modus** ⚡ NEU
  - Automatische Installation (systemd/launchd)
  - Auto-Start beim Boot
  - Auto-Restart bei Crash
  - Health-Check System
  - Log-Rotation
  - Service-Management Tool

## Systemanforderungen

### Hardware
- **Minimal:** Intel i5 / AMD Ryzen 5, 8 GB RAM
- **Empfohlen:** Intel i7 / AMD Ryzen 7, 16 GB RAM, NVIDIA GPU (CUDA)
- **Video-Input:** Blackmagic DeckLink, Elgato Cam Link oder Webcam

### Software
- **Betriebssystem:** macOS 12+, Linux (Ubuntu 20.04+), Windows 10+
- **Python:** 3.10 oder höher
- **ffmpeg:** Mit Hardware-Beschleunigung

## Installation

### 1. Repository klonen

```bash
git clone <repository-url>
cd ptz-tracking
```

### 2. Python Virtual Environment erstellen

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# oder
venv\Scripts\activate     # Windows
```

### 3. ffmpeg installieren

#### macOS
```bash
brew install ffmpeg
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg
```

#### Windows
Lade ffmpeg von [ffmpeg.org](https://ffmpeg.org/download.html) herunter und füge es zu PATH hinzu.

### 4. Python-Dependencies installieren

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. YOLO-Modell herunterladen

Das Modell wird beim ersten Start automatisch heruntergeladen. Optional manuell:

```bash
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

## Konfiguration

Bearbeite `src/config.py` für deine Hardware:

```python
# Video-Input Quelle
VIDEO_SOURCE = "ffmpeg"  # "ffmpeg", "webcam", "file"
FFMPEG_INPUT_DEVICE = "Blackmagic"  # "Blackmagic", "Elgato", "Webcam"

# Video-Einstellungen
RESOLUTION = (1920, 1080)
FPS_TARGET = 30

# YOLO-Modell
MODEL = "yolov8n.pt"  # n, s, m, l, x (nano bis extra large)
CONFIDENCE_THRESHOLD = 0.5

# Pose-Estimation 🦴
ENABLE_POSE_ESTIMATION = True
POSE_MODEL = "yolov8n-pose.pt"  # Pose-Modell (automatischer Download)
SHOW_KEYPOINTS = True
SHOW_SKELETON = True
KEYPOINT_CONFIDENCE_THRESHOLD = 0.3

# Display
DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 720
SHOW_FPS = True
```

## Verwendung

### ⚠️ Wichtig: Virtual Environment aktivieren

**Vor jedem Start** muss das Virtual Environment aktiviert werden:

```bash
source venv/bin/activate  # macOS/Linux
# oder
venv\Scripts\activate     # Windows
```

### Interaktiver Modus (Standard)

Die Anwendung kann direkt gestartet werden und verwendet die Einstellungen aus [src/config.py](src/config.py):

```bash
# Virtual Environment aktivieren
source venv/bin/activate

# Standard-Modus mit ffmpeg (Blackmagic/Elgato)
python src/main.py

# Mit Webcam (für Development/Testing)
python src/main.py --source webcam

# Mit Video-Datei
python src/main.py --source file --file path/to/video.mp4

# Vollbild-Modus
python src/main.py --fullscreen

# Debug-Modus
python src/main.py --debug

# Performance-Optimierungen
python src/main.py --source webcam --buffer-size 5  # Größerer Buffer
python src/main.py --no-threading                   # Threading deaktivieren

# Alle Optionen anzeigen
python src/main.py --help
```

**Tastenkombinationen:**
- `q` - Beenden
- `Space` - Pause/Resume
- `r` - Tracker zurücksetzen
- `f` - Vollbild-Toggle

### Headless-Modus (ohne Display)

Für Server oder Daemon-Betrieb:

```bash
python src/main.py --headless
```

### Als Service/Daemon ⚡ NEU

PTZ Tracking kann als Hintergrund-Service mit automatischem Start installiert werden:

```bash
# Linux (systemd)
sudo ./deploy/scripts/install-linux.sh
sudo systemctl start ptz-tracking
sudo systemctl enable ptz-tracking

# macOS (launchd)
sudo ./deploy/scripts/install-macos.sh
sudo launchctl start com.ptztracking.service
```

**Service-Verwaltung:**

```bash
# Mit Service-Manager (empfohlen)
./deploy/scripts/service-manager.sh start|stop|restart|status|logs

# Manuell mit systemd (Linux)
sudo systemctl status ptz-tracking
sudo journalctl -u ptz-tracking -f

# Manuell mit launchd (macOS)
sudo launchctl list | grep ptztracking
tail -f /usr/local/opt/ptz-tracking/logs/*.log
```

**Features:**
- ✅ Automatischer Start beim Boot
- ✅ Auto-Restart bei Crash
- ✅ Health-Check System
- ✅ Log-Rotation
- ✅ Einfache Deinstallation

📖 **Vollständige Service-Dokumentation:** [deploy/README.md](deploy/README.md)

### Stream-Handler Beispiel

Die Anwendung enthält ein interaktives Beispiel zur Demonstration der Video-Input-Handler:

```bash
# Stream Example starten
python examples/stream_example.py
```

**Features:**
- ✅ Webcam-Input (für Development)
- ✅ Video-Datei-Wiedergabe (mit Loop-Option)
- ✅ FFmpeg-Input (Blackmagic/Elgato)
- ✅ Live FPS-Counter
- ✅ Keyboard-Steuerung (q=Quit, f=Fullscreen)

**Hinweis für macOS Webcam:**
Kamera-Berechtigung muss in Systemeinstellungen erteilt werden:
`Systemeinstellungen → Datenschutz & Sicherheit → Kamera → Terminal aktivieren`

### Tastenkombinationen (im interaktiven Modus)

- **q** - Beenden
- **f** - Vollbild-Modus
- **p** - Pause/Resume
- **s** - Screenshot speichern (geplant)

### PTZ-Kamera-Steuerung 🎯

PTZ Tracking kann Panasonic AW-HE130 Kameras automatisch steuern, um die Person zentriert zu halten:

```bash
# 1. Kamera-IP in src/config.py konfigurieren
# PTZ_CAMERA_IP = "192.168.1.100"

# 2. Anwendung mit PTZ starten
python src/main.py --source webcam

# 3. In separatem Terminal: PTZ aktivieren über REST-API
curl http://localhost:8090/ptz/enable

# Oder im Browser:
# http://localhost:8090/ptz/enable
```

**REST-API Endpoints:**
- `GET /ptz/enable` - PTZ-Steuerung aktivieren
- `GET /ptz/disable` - PTZ-Steuerung deaktivieren
- `GET /ptz/toggle` - PTZ umschalten
- `GET /ptz/status` - Status abfragen
- `GET /ptz/home` - Zur Home-Position fahren

**Display-Anzeige:**
- **PTZ: ON** (grün) - Kamera-Steuerung aktiv
- **PTZ: OFF** (rot) - Kamera-Steuerung deaktiviert

**Features:**
- ✅ Person horizontal zentriert
- ✅ Vertikale Positionierung nach goldenem Schnitt (0.618 von unten)
- ✅ Smooth, einstellbare Bewegungen (Smoothing 0-1)
- ✅ Dead-Zone verhindert Mikrobewegungen
- ✅ Kein automatischer Zoom
- ✅ REST-API für externe Steuerung (Stream Deck, OBS, etc.)

**Test ohne Kamera:**
```bash
# PTZ-Funktionalität testen (ohne echte Kamera)
python test_ptz.py
```

📖 **Vollständige PTZ-Dokumentation:** [docs/PTZ_CONTROL.md](docs/PTZ_CONTROL.md)

## ffmpeg Video-Input Setup

### Blackmagic DeckLink (macOS)

```bash
# Verfügbare Devices auflisten
ffmpeg -f avfoundation -list_devices true -i ""

# Stream mit DeckLink
ffmpeg -f decklink -i "DeckLink SDI 4K" -pix_fmt bgr24 -f rawvideo -
```

### Elgato Cam Link (macOS)

```bash
# Stream mit Elgato
ffmpeg -f avfoundation -i "Cam Link" -pix_fmt bgr24 -f rawvideo -
```

### Webcam (Development)

```bash
# Standard Webcam
ffmpeg -f avfoundation -i "0" -pix_fmt bgr24 -f rawvideo -
```

**Hinweis:** Unter Linux verwende `-f v4l2` statt `-f avfoundation`.

## Projektstruktur

```
ptz-tracking/
├── src/
│   ├── main.py              # Haupteinstiegspunkt
│   ├── config.py            # Konfiguration
│   ├── stream/              # Video-Input Handler
│   ├── tracking/            # Person Detection & Tracking
│   ├── display/             # Visualisierung
│   └── utils/               # Logging, Performance-Messung
├── deploy/                  # Service-Deployment (systemd/launchd)
│   ├── README.md           # Deployment-Dokumentation
│   ├── systemd/            # Linux systemd Service
│   ├── launchd/            # macOS launchd Service
│   ├── logrotate/          # Log-Rotation
│   └── scripts/            # Installations-Scripts
├── examples/               # Beispiel-Code
├── tests/                  # Unit Tests
├── models/                 # YOLO-Modelle
├── requirements.txt        # Python-Dependencies
└── README.md              # Diese Datei
```

## Development

### Tests ausführen

```bash
pytest tests/
```

### Code-Formatierung

```bash
pip install black
black src/
```

### Linting

```bash
pip install flake8
flake8 src/
```

## Troubleshooting

### "No module named cv2"
```bash
pip install opencv-python
```

### "ffmpeg not found"
Stelle sicher, dass ffmpeg im PATH ist:
```bash
ffmpeg -version
```

### Niedrige FPS
- Verwende kleineres YOLO-Modell (yolov8n.pt statt yolov8x.pt)
- Aktiviere GPU-Beschleunigung (CUDA)
- Reduziere Input-Auflösung

### "No CUDA available"
Für GPU-Support:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## Performance-Optimierung

1. **GPU-Beschleunigung:** Installiere CUDA und PyTorch mit CUDA-Support
2. **Modell-Wahl:** yolov8n.pt für Speed, yolov8x.pt für Genauigkeit
3. **Auflösung:** Reduziere Display-Auflösung bei Bedarf
4. **Threading:** Nutze separate Threads für Input/Processing/Display

## Danksagungen

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [OpenCV](https://opencv.org/)
- [FFmpeg](https://ffmpeg.org/)
