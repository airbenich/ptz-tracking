# PTZ Tracking - Projektspezifikation

## Projektzusammenfassung

Eine Python-Anwendung zum Echtzeit-Tracking von Personen in Videostreams. Die Anwendung empfängt Video-Input über ffmpeg (SDI/HDMI-Quellen) und zeigt eine Live-Ansicht mit Tracking-Visualisierung und steuert PTZ Kameras.

---

## Anforderungen

### Funktionale Anforderungen

1. **Video-Input**
   - Empfang von Videostreams über ffmpeg
   - Unterstützung für SDI-Input (Blackmagic)
   - Unterstützung für HDMI-Input (Elgato Cam Link)
   - Unterstützung für Webcam-Input (für Development/Testing)
   - Robuste Stream-Verarbeitung mit Fehlerbehandlung

2. **Person Tracking**
   - Erkennung beliebiger Personen im Videostream
   - Tracking der nächsten/prominentesten Person im Bild
   - Bounding Box um erkannte Person
   - Kontinuierliches Tracking über mehrere Frames
   - **Pose-Estimation & Skeleton-Tracking** 🦴 NEU
     - 17 COCO-Keypoints (Körpergelenke)
     - Skeleton-Visualisierung mit Verbindungslinien
     - Konfidenz-basierte Keypoint-Filterung
     - Echtzeit-Pose-Erkennung

3. **Ausgabe**
   - Live-Anzeige des Videostreams
   - Visualisierung der Tracking-Bounding-Box
   - **Pose-Overlay (Keypoints + Skeleton)** 🦴 NEU
   - Anzeige von Tracking-Informationen (Position, Größe)
   - Optional: FPS-Counter

4. **Performance**
   - Echtzeit-Verarbeitung (>15 FPS)
   - Geringe Latenz zwischen Input und Ausgabe
   - Effiziente Ressourcennutzung

### Nicht-funktionale Anforderungen

- **Zuverlässigkeit:** Stabile Verarbeitung auch bei kurzen Stream-Unterbrechungen
- **Wartbarkeit:** Modularer Code mit klarer Struktur
- **Erweiterbarkeit:** Vorbereitung für zukünftige PTZ-Steuerung
- **Flexibilität:** Sowohl als interaktive Anwendung als auch als Hintergrund-Service nutzbar
- **Logging:** Console/Terminal-basiertes Logging für Debugging und Monitoring

---

## Technischer Stack

### Kern-Technologien

1. **Python 3.10+**
   - Moderne Python-Version für beste Performance

2. **ffmpeg**
   - Video-Stream-Input von verschiedenen Quellen
   - Hardware-Beschleunigung wenn verfügbar

3. **OpenCV (cv2)**
   - Video-Frame-Verarbeitung
   - Display und Visualisierung
   - Grundlegende Bildverarbeitung

4. **YOLO (Ultralytics YOLOv8)**
   - Schnelle und genaue Person Detection
   - Echtzeit-Performance
   - Vortrainierte Modelle verfügbar
   - GPU-Unterstützung (CUDA)

5. **NumPy**
   - Effiziente Array-Operationen
   - Frame-Manipulation

### Alternative/Zusätzliche Bibliotheken

- **DeepSORT** (optional): Für verbessertes Multi-Frame-Tracking
- **PyTorch**: Backend für YOLO-Modelle
- **Threading/Asyncio**: Für parallele Video-Verarbeitung

---

## Architektur

### Komponenten-Übersicht

```
┌─────────────────────────────────────────────────────┐
│                   Main Application                   │
└─────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Stream     │  │   Person     │  │   Display    │
│   Handler    │  │   Tracker    │  │   Manager    │
└──────────────┘  └──────────────┘  └──────────────┘
        │                │                │
        ▼                ▼                ▼
  ffmpeg Input    YOLO Detection   OpenCV Display
```

### Modul-Struktur

```
ptz-tracking/
│
├── PROJECT_SPECIFICATION.md
├── README.md
├── requirements.txt
├── .gitignore
│
├── src/
│   ├── __init__.py
│   ├── main.py                 # Haupteinstiegspunkt
│   ├── config.py               # Konfigurationsverwaltung
│   │
│   ├── stream/
│   │   ├── __init__.py
│   │   ├── ffmpeg_handler.py  # ffmpeg Stream-Verarbeitung
│   │   ├── video_source.py    # Abstrakte Video-Quelle
│   │   └── threaded_capture.py # Threading für Video-Capture
│   │
│   ├── tracking/
│   │   ├── __init__.py
│   │   ├── person_detector.py # YOLO-basierte Detection
│   │   └── tracker.py         # Tracking-Logik
│   │
│   ├── display/
│   │   ├── __init__.py
│   │   └── visualizer.py      # OpenCV Display
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py          # Logging-Konfiguration
│       └── performance_manager.py  # Performance-Optimierung
│
├── deploy/                     # Service-Deployment
│   ├── README.md              # Deployment-Dokumentation
│   ├── systemd/               # Linux systemd Service
│   │   └── ptz-tracking.service
│   ├── launchd/               # macOS launchd Service
│   │   └── com.ptztracking.service.plist
│   ├── logrotate/             # Log-Rotation
│   │   └── ptz-tracking
│   └── scripts/               # Installations-Scripts
│       ├── install-linux.sh
│       ├── install-macos.sh
│       ├── uninstall-linux.sh
│       ├── uninstall-macos.sh
│       ├── service-manager.sh
│       └── health-check.py
│
├── examples/                   # Beispiel-Scripts
│   ├── stream_example.py
│   ├── detection_example.py
│   └── tracking_example.py
│
├── tests/
│   ├── __init__.py
│   └── test_tracking.py
│
├── models/
│   └── README.md              # Info zu verwendeten Modellen
│
├── logs/                      # Log-Dateien (automatisch erstellt)
└── output/                    # Optional: Screenshots, Recordings
```

---

## Referenzen

- [Ultralytics YOLOv8 Dokumentation](https://docs.ultralytics.com/)
- [OpenCV Python Tutorial](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
- [ffmpeg Dokumentation](https://ffmpeg.org/documentation.html)
- [DeepSORT Paper](https://arxiv.org/abs/1703.07402)
