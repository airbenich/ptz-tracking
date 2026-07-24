# PTZ-Steuerung für Panasonic AW-HE130

## Übersicht

Die PTZ-Tracking-Steuerung ermöglicht automatisches Schwenken und Neigen (Pan/Tilt) der Panasonic AW-HE130 Kamera, um eine Person im Bild zu zentrieren.

## Features

- **Automatische Person-Zentrierung** - Person wird horizontal in der Mitte gehalten  
- **Goldener Schnitt** - Vertikale Positionierung nach goldenem Schnitt (0.618 von unten)  
- **Broadcast-Quality Movement** - Progressive Speed-basierte Steuerung für smooth, professionelle Kamerabewegungen  
- **Progressive Annäherung** - Je näher am Ziel, desto langsamer die Bewegung  
- **Speed-Ramping** - Exponentiell verlangsamend für natürliche Bewegungen  
- **Dead-Zone** - Vermeidet Mikrobewegungen bei kleinen Abweichungen  
- **REST-API Steuerung** - Ein-/Ausschalten über HTTP GET Requests  
- **Status-Anzeige** - PTZ-Status sichtbar im Visualizer  
- **Kein automatischer Zoom** - Zoom-Steuerung bleibt beim Operator  
- **GStreamer-Optimiert** - 70% niedrigere Latenz für reaktiveres Tracking  

## Video-Backend für optimale Performance

### GStreamer (EMPFOHLEN)

**Vorteile für PTZ-Tracking:**
- **Latenz: 30-50ms** (vs. 100-200ms mit FFmpeg)
- **70% schnellere Reaktion** auf Personenbewegungen
- **Präziseres Tracking** durch niedrigere Verzögerung
- **Native DeckLink-Integration** für professionelle Setups

**Konfiguration:**
```python
# src/config.py
VIDEO_SOURCE = "gstreamer"  # EMPFOHLEN für PTZ
GSTREAMER_INPUT_DEVICE = "Blackmagic"
DECKLINK_CONNECTION = "sdi"
DECKLINK_MODE = "1080p25"
```

**Installation:**
```bash
chmod +x install-gstreamer.sh
./install-gstreamer.sh
```

**Details:** [GSTREAMER_QUICKSTART.md](../GSTREAMER_QUICKSTART.md)

### FFmpeg (Fallback)

**Charakteristik:**
- **Latenz: 100-200ms**
- **Funktioniert zuverlässig** für weniger kritische Anwendungen
- **Einfaches Setup**

**Konfiguration:**
```python
# src/config.py
VIDEO_SOURCE = "ffmpeg"
FFMPEG_INPUT_DEVICE = "Blackmagic"
```  

## Konfiguration

Alle PTZ-Einstellungen finden sich in `src/config.py`:

```python
# PTZ aktivieren/deaktivieren
ENABLE_PTZ = True

# Kamera-Verbindung
PTZ_CAMERA_IP = "192.168.1.100"
PTZ_CAMERA_PORT = 80

# Zielposition
PTZ_TARGET_X = 0.5     # Horizontal: 0.5 = Mitte
PTZ_TARGET_Y = 0.382   # Vertikal: 0.382 = Goldener Schnitt (1 - 0.618)

# Dead-Zone (Bereich ohne Korrektur)
PTZ_DEADZONE_X = 0.02  # ±2% horizontal (enger für präzises Tracking)
PTZ_DEADZONE_Y = 0.02  # ±2% vertikal

# Speed-basierte Steuerung (PTS-Befehle)
# Speed-Range: 01-99, wobei 50=Stop, <50=links/unten, >50=rechts/oben
PTZ_MAX_SPEED = 20      # Maximale Geschwindigkeit (bei großer Distanz)
PTZ_MIN_SPEED = 2       # Minimale Geschwindigkeit (nahe am Ziel)
PTZ_SPEED_RAMP = 0.15   # Speed-Ramping-Faktor (0.0-1.0, höher=progressiver)

# Smoothing für Speed-Änderungen (0.0-1.0)
# Verhindert abrupte Geschwindigkeitswechsel für broadcast-quality
PTZ_SPEED_SMOOTHING = 0.3  # 30% neue Speed, 70% alte Speed

# Update-Interval (130ms Minimum laut Panasonic Spec)
PTZ_UPDATE_INTERVAL = 0.13

# PTZ Speed-Neutral (50 = Stop)

# REST-API
PTZ_REST_ENABLED = True
PTZ_REST_HOST = "0.0.0.0"
PTZ_REST_PORT = 8080

# Initial-Status
PTZ_ENABLED_ON_START = False  # Startet deaktiviert
```

## Goldener Schnitt

Die vertikale Positionierung nutzt den goldenen Schnitt (φ ≈ 1.618):
- Person soll bei **0.618 von unten** positioniert sein
- In der Config: `PTZ_TARGET_Y = 0.382` (= 1 - 0.618)
- Ergebnis: Person im oberen Drittel, ästhetisch ansprechend

```
┌─────────────────┐
│                 │  ← 0.0 (oben)
│                 │
│     👤          │  ← 0.382 (goldener Schnitt - Zielpunkt)
│                 │
│                 │
└─────────────────┘  ← 1.0 (unten)
```

## REST-API Endpoints

Der REST-Server läuft standardmäßig auf Port 8080:

### PTZ aktivieren
```bash
curl http://localhost:8080/ptz/enable
```

Response:
```json
{
  "success": true,
  "message": "PTZ-Steuerung aktiviert",
  "enabled": true
}
```

### PTZ deaktivieren
```bash
curl http://localhost:8080/ptz/disable
```

### PTZ umschalten (Toggle)
```bash
curl http://localhost:8080/ptz/toggle
```

### Status abfragen
```bash
curl http://localhost:8080/ptz/status
```

Response:
```json
{
  "success": true,
  "status": {
    "enabled": true,
    "camera_ip": "192.168.1.100",
    "current_pan": 2048,
    "current_tilt": 2048,
    "target_pan": 2100,
    "target_tilt": 2000,
    "smoothing": 0.7,
    "pan_speed": 15,
    "tilt_speed": 15
  }
}
```

### Home-Position anfahren
```bash
curl http://localhost:8080/ptz/home
```

## Verwendung

### Starten mit PTZ-Steuerung

```bash
# Mit GStreamer (EMPFOHLEN für beste Reaktionszeit)
python src/main.py --source gstreamer --device Blackmagic

# Mit FFmpeg (Fallback)
python src/main.py --source ffmpeg --device Blackmagic

# Mit Webcam für Testing
python src/main.py --source webcam
```

Die Anwendung:
1. Startet mit **PTZ deaktiviert** (`PTZ: OFF` rot im Display)
2. Startet REST-Server auf Port 8080
3. Wartet auf Aktivierung über REST-API

### PTZ aktivieren

In einem zweiten Terminal oder Browser:

```bash
# Terminal
curl http://localhost:8080/ptz/enable

# Oder im Browser
http://localhost:8080/ptz/enable
```

Im Display wechselt der Status zu **`PTZ: ON`** (grün).

### PTZ-Status im Display

Oben links im Visualizer wird der PTZ-Status angezeigt:

```
PTZ: ON   (grün = aktiv)
PTZ: OFF  (rot = deaktiviert)
```

## Funktionsweise

### 1. Person-Erkennung
- YOLOv8 erkennt Person im Frame
- Bounding-Box definiert Position

### 2. Zielposition berechnen
```python
# Person-Zentrum ermitteln
person_x = (bbox_x1 + bbox_x2) / 2
person_y = (bbox_y1 + bbox_y2) / 2

# Abweichung von Zielposition
delta_x = person_x / frame_width - PTZ_TARGET_X
delta_y = person_y / frame_height - PTZ_TARGET_Y

# Dead-Zone: Kleine Abweichungen ignorieren
if abs(delta_x) < PTZ_DEADZONE_X:
    delta_x = 0
```

### 3. Smoothing anwenden
```python
# Exponential Smoothing
target_pan = smoothing * old_target + (1 - smoothing) * new_target
```

### 4. PTZ-Speed-Befehl senden
```python
# Panasonic CGI-Befehle für Speed-basierte Steuerung
# Format: /cgi-bin/aw_ptz?cmd=%23PTS{pan_speed}{tilt_speed}&res=1
# Speed: 01-99 (2-stellig Dezimal), 50=Stop
url = f"http://{camera_ip}/cgi-bin/aw_ptz?cmd=%23PTS{pan_speed:02d}{tilt_speed:02d}&res=1"
requests.get(url, timeout=0.5)
```

## Panasonic AW-HE130 CGI-Befehle

Die Kamera nutzt HTTP-basierte CGI-Befehle gemäß Panasonic Interface Specification.

### Speed-basierte Steuerung (PTS) ⭐️ **VERWENDET**
```
GET /cgi-bin/aw_ptz?cmd=%23PTS{pan_speed}{tilt_speed}&res=1
```

- **{pan_speed}**: 01-99 (2-stellig Dezimal)
  - 01 = maximale Geschwindigkeit nach links
  - 50 = Stop
  - 99 = maximale Geschwindigkeit nach rechts
- **{tilt_speed}**: 01-99 (2-stellig Dezimal)
  - 01 = maximale Geschwindigkeit nach unten
  - 50 = Stop
  - 99 = maximale Geschwindigkeit nach oben

**Broadcast-Quality Tracking:**
- Progressive Annäherung: Speed reduziert sich exponentiell je näher am Ziel
- Smooth Ramping: Speed-Änderungen werden geglättet (PTZ_SPEED_SMOOTHING)
- Continuous Movement: Kamera bewegt sich flüssig ohne Sprünge

Beispiele:
```bash
# Stop (Kamera hält an)
curl "http://192.168.1.100/cgi-bin/aw_ptz?cmd=%23PTS5050&res=1"

# Langsam nach rechts und oben
curl "http://192.168.1.100/cgi-bin/aw_ptz?cmd=%23PTS5560&res=1"

# Schnell nach links
curl "http://192.168.1.100/cgi-bin/aw_ptz?cmd=%23PTS2050&res=1"
```

### Absolute Positionierung (APC/ATC) - Nicht verwendet
Für Preset-Recall geeignet, aber nicht für smooth Tracking:
```
GET /cgi-bin/aw_ptz?cmd=%23APC{pan}ATC{tilt}&res=1
```

- **{pan}**: 00000-0FFFF (5-stellig Hex), Mitte = 08000
- **{tilt}**: 00000-0FFFF (5-stellig Hex), Mitte = 08000

Beispiele:
```bash
# Kamera zur Mitte fahren
curl "http://192.168.1.100/cgi-bin/aw_ptz?cmd=%23APC08000ATC08000&res=1"

# Kamera nach rechts oben
curl "http://192.168.1.100/cgi-bin/aw_ptz?cmd=%23APC0A000ATC06000&res=1"
```

## Performance

### Mit GStreamer (EMPFOHLEN)
- **Update-Rate**: 7.7 Hz (alle 130ms, Minimum laut Panasonic Spec)
- **Video-Latenz**: 30-50ms (DeckLink SDI)
- **End-to-End Latenz**: ~60-80ms (Video + Detection + PTZ)
- **Reaktionszeit**: ⚡ **Hervorragend** für schnelle Bewegungen

### Mit FFmpeg (Fallback)
- **Update-Rate**: 7.7 Hz (alle 130ms)
- **Video-Latenz**: 100-200ms
- **End-to-End Latenz**: ~180-250ms (Video + Detection + PTZ)
- **Reaktionszeit**: 🐢 **Ausreichend** für langsame Bewegungen

### Allgemeine Parameter
- **Minimale Bewegung**: 10 Pan/Tilt Units (vermeidet Jitter)
- **Smoothing**: Default 0.7 (70% alte Position, 30% neue Position)
- **Timeout**: 500ms pro HTTP-Request
- **Command Delay**: 130ms Mindest-Abstand zwischen Befehlen (Panasonic-Vorgabe)

## Troubleshooting

### Kamera nicht erreichbar

**Symptom**: Keine PTZ-Bewegung, Logs zeigen "Verbindung fehlgeschlagen"

**Lösung**:
1. Kamera-IP prüfen: `ping 192.168.1.100`
2. IP in `config.py` anpassen
3. Firewall-Regeln prüfen

### PTZ zu ruckartig

**Symptom**: Kamera bewegt sich in Sprüngen oder zu abrupt

**Lösung**:
```python
# In config.py erhöhen:
PTZ_SPEED_SMOOTHING = 0.5  # Mehr Speed-Glättung (0.3 → 0.5)
PTZ_DEADZONE_X = 0.05      # Größere Dead-Zone
PTZ_DEADZONE_Y = 0.05
PTZ_MAX_SPEED = 15         # Reduzierte Max-Speed
```

### PTZ zu träge

**Symptom**: Kamera folgt Person zu langsam oder reagiert verzögert

**Lösung 1: GStreamer verwenden** (⚡ Beste Lösung)
```python
# src/config.py
VIDEO_SOURCE = "gstreamer"  # 70% niedrigere Latenz!
```

**Lösung 2: Geschwindigkeit erhöhen**
```python
# In config.py anpassen:
PTZ_SPEED_SMOOTHING = 0.1  # Weniger Glättung (schnellere Reaktion)
PTZ_MAX_SPEED = 30         # Höhere Max-Geschwindigkeit
PTZ_MIN_SPEED = 3          # Höhere Min-Geschwindigkeit
PTZ_SPEED_RAMP = 0.1       # Weniger progressiv (direkter)
```

### PTZ zu schnell / unkontrolliert

**Symptom**: Kamera "schießt" über Ziel hinaus oder überkompensiert

**Lösung**:
```python
# In config.py reduzieren:
PTZ_MAX_SPEED = 12         # Niedrigere Max-Speed
PTZ_SPEED_RAMP = 0.25      # Stärker progressiv (sanfter)
PTZ_DEADZONE_X = 0.03      # Engere Dead-Zone für präziseres Tracking
```

### REST-Server startet nicht

**Symptom**: "Port bereits belegt"

**Lösung**:
```python
# In config.py anderen Port wählen:
PTZ_REST_PORT = 8081
```

## Integration in externe Systeme

### Stream Deck Integration

Erstelle Buttons für PTZ-Steuerung:

1. **PTZ ON** Button:
   - System → Open URL
   - URL: `http://192.168.1.10:8080/ptz/enable`

2. **PTZ OFF** Button:
   - System → Open URL
   - URL: `http://192.168.1.10:8080/ptz/disable`

3. **PTZ Home** Button:
   - System → Open URL
   - URL: `http://192.168.1.10:8080/ptz/home`

### OBS Integration

Verwende OBS-Websocket + Python-Script:

```python
import requests

# PTZ aktivieren wenn Szene gewechselt wird
def on_scene_change(scene_name):
    if scene_name == "Presenter":
        requests.get("http://localhost:8080/ptz/enable")
    else:
        requests.get("http://localhost:8080/ptz/disable")
```

### HTTP-Trigger über Companion

Bitfocus Companion kann HTTP GET Requests senden:

1. Neuen Button erstellen
2. Action hinzufügen: "Generic HTTP Request"
3. URL: `http://192.168.1.10:8080/ptz/toggle`
4. Method: GET

## Erweiterte Konfiguration

### Mehrere Kameras

Für mehrere Kameras separate PTZ-Controller instanziieren:

```python
# In custom code (nicht standardmäßig)
camera1 = PTZController(camera_ip="192.168.1.100")
camera2 = PTZController(camera_ip="192.168.1.101")
```

### Custom Tracking-Logik

Für spezielle Anforderungen kann die `calculate_target_position()` Methode angepasst werden:

```python
# In src/ptz/ptz_controller.py
def calculate_target_position(self, detection, frame_width, frame_height):
    # Custom logic hier
    # z.B. Person immer links statt zentriert
    target_x = 0.33  # Linkes Drittel statt Mitte
    ...
```

## Sicherheit

**Wichtig**: Der REST-Server hat keine Authentifizierung!

Für Produktionsumgebungen:
1. Firewall-Regeln einrichten (nur trusted IPs)
2. Reverse-Proxy mit Basic Auth (nginx)
3. VPN für Fernzugriff

## Lizenz

Teil des PTZ-Tracking Projekts (siehe Haupt-README)
