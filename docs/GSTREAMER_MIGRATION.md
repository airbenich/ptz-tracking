# GStreamer Migration Guide

## Übersicht

Dieser Guide beschreibt die Migration von FFmpeg zu GStreamer für das PTZ Tracking Projekt.

**Ziel:** Bessere Performance, niedrigere Latenz und native Blackmagic DeckLink-Integration für professionelles PTZ-Tracking.

---

## Vorteile der GStreamer-Migration

### Performance-Verbesserungen

| Metrik | FFmpeg | GStreamer | Verbesserung |
|--------|--------|-----------|--------------|
| **Latenz (DeckLink)** | ~100-200ms | ~30-50ms | **60-70% reduziert** |
| **CPU-Last** | Mittel-Hoch | Niedrig-Mittel | **~20-30% weniger** |
| **Buffer-Kontrolle** | Limited | Granular | **Vollständig konfigurierbar** |
| **Hardware-Accel** | Nein | Ja | **GPU-Unterstützung** |

### Funktionale Vorteile

- **Native DeckLink-Integration** via `decklinkvideosrc`
- **Zero-Copy Buffer-Handling** für minimale Latenz
- **Granulare Latenz-Kontrolle** (`max-buffers`, `drop`, `latency`)
- **Hardware-beschleunigte Konvertierung** (GPU)
- **Bessere Pipeline-Flexibilität**
- **Professionelle Broadcast-Quality**

---

## Migrations-Roadmap

### Phase 1: Installation & Setup

**Schritt 1.1: GStreamer installieren**

```bash
# Installations-Skript ausführen
chmod +x install-gstreamer.sh
./install-gstreamer.sh
```

**Schritt 1.2: Python-Dependencies installieren**

```bash
pip install -r requirements.txt
```

**Schritt 1.3: Blackmagic Desktop Video SDK (für DeckLink)**

1. Download: https://www.blackmagicdesign.com/support/
2. Installiere **Desktop Video** Software
3. Verifiziere Installation:
   ```bash
   gst-inspect-1.0 decklinkvideosrc
   ```

---

### Phase 2: Konfiguration

**Schritt 2.1: Video-Quelle auf GStreamer umstellen**

Editiere `src/config.py`:

```python
# Alte Konfiguration (FFmpeg)
VIDEO_SOURCE = "ffmpeg"

# Neue Konfiguration (GStreamer)
VIDEO_SOURCE = "gstreamer"
```

**Schritt 2.2: Device-Konfiguration**

```python
# GStreamer Input-Device
GSTREAMER_INPUT_DEVICE = "Blackmagic"  # oder "Elgato", "Webcam"

# Device-Nummern (für mehrere Devices)
GSTREAMER_DEVICE_NUMBERS = {
    "Blackmagic": 0,  # DeckLink Device 0
    "Elgato": 0,      # V4L2/AVFoundation Device 0
    "Webcam": 0,
}

# DeckLink-spezifisch
DECKLINK_CONNECTION = "sdi"     # sdi, hdmi, optical-sdi
DECKLINK_MODE = "1080p25"       # Muss mit FPS_TARGET übereinstimmen
```

**Schritt 2.3: Performance-Tuning**

```python
# Buffer-Einstellungen für minimale Latenz
GSTREAMER_MAX_BUFFERS = 2           # Nur 2 Frames puffern
GSTREAMER_DROP_OLD_BUFFERS = True   # Alte Frames verwerfen
GSTREAMER_BUFFER_LATENCY = 0        # Minimale Latenz
```

---

### Phase 3: Testing

**Schritt 3.1: GStreamer-Handler testen**

```bash
# Test mit Device-Listing
python3 src/stream/gstreamer_handler.py
```

**Schritt 3.2: Pipeline direkt testen (gst-launch)**

```bash
# DeckLink Test (Blackmagic)
gst-launch-1.0 decklinkvideosrc device-number=0 connection=sdi mode=1080p25 \
  ! videoconvert ! autovideosink

# V4L2 Test (Linux, Elgato)
gst-launch-1.0 v4l2src device=/dev/video0 \
  ! image/jpeg,width=1920,height=1080 ! jpegdec \
  ! videoconvert ! autovideosink

# AVFoundation Test (macOS, Elgato)
gst-launch-1.0 avfvideosrc device-index=0 \
  ! videoconvert ! autovideosink
```

**Schritt 3.3: Stream Factory testen**

```bash
python3 src/stream/stream_factory.py
```

**Schritt 3.4: Vollständiger Integration-Test**

```bash
# PTZ Tracking mit GStreamer starten
python3 src/main.py --source gstreamer --device Blackmagic
```

---

### Phase 4: Deployment

**Schritt 4.1: macOS Deployment**

```bash
# GStreamer via Homebrew
brew install gstreamer gst-python gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly

# Blackmagic SDK
# Download und installiere von Blackmagic Website

# Python Environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Schritt 4.2: Linux Deployment**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    python3-gi \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-decklink

# Python Environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Schritt 4.3: Systemd Service (Linux)**

```bash
# Service installieren (nutzt bestehende Deployment-Skripte)
sudo deploy/scripts/install-linux.sh

# Konfiguration anpassen
sudo nano /etc/ptz-tracking/config.py
# VIDEO_SOURCE = "gstreamer" setzen

# Service neu starten
sudo systemctl restart ptz-tracking
```

---

## Hardware-Spezifische Konfiguration

### Blackmagic DeckLink

**Unterstützte Modelle:**
- DeckLink Mini Recorder
- DeckLink SDI 4K
- DeckLink Duo 2
- DeckLink Studio 4K
- Intensity Pro 4K

**GStreamer Pipeline:**
```python
pipeline = (
    f"decklinkvideosrc device-number=0 connection=sdi mode=1080p25 "
    f"! videoconvert "
    f"! video/x-raw,format=BGR,width=1920,height=1080,framerate=25/1 "
    f"! appsink name=sink max-buffers=2 drop=true"
)
```

**Verfügbare Modi:**
```bash
# Alle verfügbaren Modi anzeigen
gst-inspect-1.0 decklinkvideosrc | grep -A 100 "mode"
```

Häufige Modi:
- `1080p25` - 1920x1080 @ 25 FPS
- `1080p50` - 1920x1080 @ 50 FPS
- `1080i50` - 1920x1080 @ 50 FPS interlaced
- `2160p25` - 3840x2160 @ 25 FPS (4K)

**Verbindungstypen:**
- `sdi` - Standard SDI
- `hdmi` - HDMI
- `optical-sdi` - Optical SDI (Fiber)
- `component` - Component Video
- `composite` - Composite Video

### Elgato Cam Link 4K

**Linux (V4L2):**
```python
GSTREAMER_INPUT_DEVICE = "Elgato"
GSTREAMER_DEVICE_NUMBERS = {"Elgato": 0}  # /dev/video0
```

**Pipeline:**
```python
pipeline = (
    f"v4l2src device=/dev/video0 "
    f"! image/jpeg,width=1920,height=1080,framerate=25/1 "
    f"! jpegdec "
    f"! videoconvert "
    f"! video/x-raw,format=BGR "
    f"! appsink name=sink max-buffers=2 drop=true"
)
```

**macOS (AVFoundation):**
```python
pipeline = (
    f"avfvideosrc device-index=0 "
    f"! video/x-raw,width=1920,height=1080,framerate=25/1 "
    f"! videoconvert "
    f"! video/x-raw,format=BGR "
    f"! appsink name=sink max-buffers=2 drop=true"
)
```

**Device-Erkennung (macOS):**
```bash
gst-device-monitor-1.0 Video | grep -i "cam link"
```

---

## Troubleshooting

### Problem: GStreamer nicht gefunden

**Symptom:**
```
ImportError: cannot import name 'Gst' from 'gi.repository'
```

**Lösung:**
```bash
# macOS
brew install gst-python

# Linux
sudo apt-get install python3-gi
```

### Problem: decklinkvideosrc nicht verfügbar

**Symptom:**
```
gst-inspect-1.0: No such element or plugin 'decklinkvideosrc'
```

**Lösung:**
1. Installiere Blackmagic Desktop Video SDK
2. Linux: `sudo apt-get install gstreamer1.0-decklink`
3. Verifiziere: `gst-inspect-1.0 decklinkvideosrc`

### Problem: Pipeline startet nicht

**Symptom:**
```
Pipeline konnte nicht gestartet werden
```

**Debug:**
```bash
# Setze GST_DEBUG für detaillierte Logs
export GST_DEBUG=3
python3 src/main.py

# Teste Pipeline direkt
gst-launch-1.0 -v decklinkvideosrc device-number=0 ! fakesink
```

### Problem: Keine Frames in appsink

**Symptom:**
```python
self.frame_ready == False  # Keine Frames verfügbar
```

**Lösung:**
```python
# Prüfe Callback-Registrierung
self.appsink.set_property('emit-signals', True)
self.appsink.connect('new-sample', self._on_new_sample)

# Debug-Output
print(f"Pipeline State: {self.pipeline.get_state(timeout=0)}")
```

### Problem: Hohe Latenz

**Symptom:**
PTZ-Tracking reagiert verzögert

**Optimierung:**
```python
# config.py
GSTREAMER_MAX_BUFFERS = 1        # Nur 1 Frame puffern
GSTREAMER_DROP_OLD_BUFFERS = True
GSTREAMER_BUFFER_LATENCY = 0     # Keine zusätzliche Latenz

# Pipeline-String (appsink)
sync=false  # Deaktiviere Synchronisation für minimale Latenz
```

---

## Performance-Monitoring

### Latenz messen

```python
import time

# In GStreamerHandler._on_new_sample()
def _on_new_sample(self, appsink):
    timestamp = time.time()
    sample = appsink.emit('pull-sample')
    
    # Buffer-Timestamp
    buffer = sample.get_buffer()
    pts = buffer.pts
    
    # Latenz berechnen
    current_time = time.time()
    latency = (current_time - timestamp) * 1000  # ms
    
    logger.debug(f"Frame Latency: {latency:.2f}ms")
    
    return Gst.FlowReturn.OK
```

### FPS-Monitoring

```python
# In main.py bereits implementiert
if visualizer:
    fps = visualizer.fps_counter.get_average_fps()
    logger.info(f"Average FPS: {fps:.1f}")
```

### System-Ressourcen

```python
# In main.py bereits verfügbar
from src.utils.performance import SystemStats

stats = SystemStats()
logger.info(f"CPU: {stats.get_cpu_usage():.1f}%")
logger.info(f"RAM: {stats.get_memory_usage():.1f}%")
```

---

## Rollback-Plan

Falls die Migration fehlschlägt, kann jederzeit auf FFmpeg zurückgewechselt werden:

```python
# src/config.py
VIDEO_SOURCE = "ffmpeg"  # Zurück zu FFmpeg
```

FFmpeg-Handler bleibt vollständig erhalten und funktionsfähig.

---

## Checkliste

### Pre-Migration

- [ ] Backup der aktuellen Konfiguration erstellt
- [ ] FFmpeg-Setup dokumentiert (funktioniert)
- [ ] Blackmagic Desktop Video SDK verfügbar
- [ ] GStreamer systemweit installiert

### Migration

- [ ] `install-gstreamer.sh` ausgeführt
- [ ] Python-Dependencies installiert (`pip install -r requirements.txt`)
- [ ] `src/config.py` aktualisiert (`VIDEO_SOURCE = "gstreamer"`)
- [ ] GStreamer-Handler getestet (`python3 src/stream/gstreamer_handler.py`)
- [ ] Pipeline-Test erfolgreich (`gst-launch-1.0 decklinkvideosrc ...`)

### Post-Migration Testing

- [ ] Stream Factory Test OK
- [ ] Full Integration Test OK (`python3 src/main.py`)
- [ ] PTZ-Tracking funktioniert
- [ ] Latenz gemessen und akzeptabel
- [ ] FPS stabil und ausreichend
- [ ] Keine Frame-Drops unter Last

### Deployment

- [ ] Systemd Service aktualisiert (Linux)
- [ ] LaunchD Service aktualisiert (macOS)
- [ ] Monitoring aktiviert
- [ ] Dokumentation aktualisiert

---

## Weitere Ressourcen

### Offizielle Dokumentation

- **GStreamer:** https://gstreamer.freedesktop.org/documentation/
- **PyGObject:** https://pygobject.readthedocs.io/
- **Blackmagic DeckLink SDK:** https://www.blackmagicdesign.com/support/

### Nützliche Befehle

```bash
# Alle verfügbaren Plugins anzeigen
gst-inspect-1.0

# Spezifisches Plugin inspizieren
gst-inspect-1.0 decklinkvideosrc

# Verfügbare Video-Devices anzeigen
gst-device-monitor-1.0 Video

# Pipeline mit Debug-Output testen
GST_DEBUG=3 gst-launch-1.0 decklinkvideosrc ! fakesink

# Pipeline-Graph visualisieren
GST_DEBUG_DUMP_DOT_DIR=. gst-launch-1.0 decklinkvideosrc ! fakesink
dot -Tpng pipeline.dot -o pipeline.png
```

---

## Migration abgeschlossen

Nach erfolgreicher Migration sollte das System:

- DeckLink & Elgato nativ über GStreamer unterstützen
- 60-70% niedrigere Latenz haben
- Stabilere Framerate aufweisen
- Weniger CPU-Last generieren
- Unter macOS und Linux funktionieren
- Fallback auf FFmpeg ermöglichen

**Support:** Bei Fragen oder Problemen siehe Troubleshooting-Sektion oder öffne ein Issue im Repository.
