# GStreamer Migration - Quick Start

## Schnellstart

### 1. GStreamer installieren

```bash
chmod +x install-gstreamer.sh
./install-gstreamer.sh
```

### 2. Python-Dependencies

```bash
pip install -r requirements.txt
```

### 3. Blackmagic DeckLink SDK (für DeckLink)

Download: https://www.blackmagicdesign.com/support/
Installiere: **Desktop Video** Software

### 4. Konfiguration

Editiere `src/config.py`:

```python
# Video-Quelle auf GStreamer umstellen
VIDEO_SOURCE = "gstreamer"

# Device-Typ
GSTREAMER_INPUT_DEVICE = "Blackmagic"  # oder "Elgato", "Webcam"

# DeckLink-Einstellungen (nur für Blackmagic)
DECKLINK_CONNECTION = "sdi"      # sdi, hdmi, optical-sdi
DECKLINK_MODE = "1080p25"        # Muss mit FPS_TARGET übereinstimmen
```

### 5. Testen

```bash
# Device-Liste anzeigen
gst-device-monitor-1.0 Video

# GStreamer-Handler testen
python3 src/stream/gstreamer_handler.py

# PTZ Tracking starten
python3 src/main.py
```

## System-Anforderungen

### macOS
- macOS 11+ (Big Sur oder neuer)
- Homebrew
- Python 3.8+
- Blackmagic Desktop Video (für DeckLink)

### Linux
- Ubuntu 20.04+ / Debian 11+
- Python 3.8+
- Blackmagic Desktop Video (für DeckLink)

## Unterstützte Hardware

### Blackmagic DeckLink
- Native Integration via `decklinkvideosrc`
- Verbindungen: SDI, HDMI, Optical SDI
- Modi: 1080p25, 1080p50, 1080i50, 2160p25, etc.
- **Beste Performance und Latenz**

### Elgato Cam Link 4K
- Linux: V4L2 (`v4l2src`)
- macOS: AVFoundation (`avfvideosrc`)
- Automatische Device-Erkennung

### USB-Capture-Devices
- Alle V4L2-kompatiblen Devices (Linux)
- Alle AVFoundation-kompatiblen Devices (macOS)

## Performance-Vorteile

| Metrik | FFmpeg | GStreamer | Verbesserung |
|--------|--------|-----------|--------------|
| Latenz (DeckLink) | ~100-200ms | ~30-50ms | **-70%** |
| CPU-Last | Mittel | Niedrig | **-30%** |
| Buffer-Kontrolle | ❌ | ✅ | **Vollständig** |
| Hardware-Accel | ❌ | ✅ | **GPU** |

## Troubleshooting

### GStreamer nicht gefunden
```bash
# macOS
brew install gst-python

# Linux
sudo apt-get install python3-gi
```

### decklinkvideosrc fehlt
```bash
# Blackmagic Desktop Video SDK installieren
# https://www.blackmagicdesign.com/support/

# Linux
sudo apt-get install gstreamer1.0-decklink

# Verifizieren
gst-inspect-1.0 decklinkvideosrc
```

### Pipeline startet nicht
```bash
# Debug-Modus aktivieren
export GST_DEBUG=3
python3 src/main.py

# Pipeline direkt testen
gst-launch-1.0 -v decklinkvideosrc device-number=0 ! fakesink
```

## Dokumentation

Vollständige Dokumentation: [docs/GSTREAMER_MIGRATION.md](docs/GSTREAMER_MIGRATION.md)

- Installation & Setup
- Konfiguration
- Hardware-spezifische Pipelines
- Performance-Tuning
- Troubleshooting
- Rollback-Plan

## Rollback zu FFmpeg

Falls Probleme auftreten:

```python
# src/config.py
VIDEO_SOURCE = "ffmpeg"
```

FFmpeg bleibt als Fallback vollständig funktionsfähig.

## Neue Dateien

```
ptz-tracking/
├── src/stream/
│   └── gstreamer_handler.py          # GStreamer Video-Handler
├── docs/
│   └── GSTREAMER_MIGRATION.md        # Vollständige Dokumentation
├── install-gstreamer.sh               # Installations-Skript
└── GSTREAMER_QUICKSTART.md           # Diese Datei
```

## Checkliste

- [ ] GStreamer installiert (`./install-gstreamer.sh`)
- [ ] Python-Dependencies installiert (`pip install -r requirements.txt`)
- [ ] Blackmagic SDK installiert (für DeckLink)
- [ ] `VIDEO_SOURCE = "gstreamer"` in `src/config.py`
- [ ] Device-Test erfolgreich (`gst-device-monitor-1.0 Video`)
- [ ] Handler-Test erfolgreich (`python3 src/stream/gstreamer_handler.py`)
- [ ] PTZ Tracking läuft (`python3 src/main.py`)

---

**Bei Fragen:** Siehe [docs/GSTREAMER_MIGRATION.md](docs/GSTREAMER_MIGRATION.md) oder öffne ein Issue.
