# PTZ Tracking Features

Vollständige Dokumentation der Hauptfunktionen: PTZ-Kamerasteuerung und Multi-Person-Tracking.

---

## Inhaltsverzeichnis

1. [PTZ-Steuerung](#ptz-steuerung)
   - [Übersicht](#übersicht)
   - [Features](#ptz-features)
   - [Konfiguration](#ptz-konfiguration)
   - [REST-API](#ptz-rest-api)
   - [Performance](#ptz-performance)
   - [Troubleshooting](#ptz-troubleshooting)
2. [Multi-Person Tracking](#multi-person-tracking)
   - [Übersicht](#multi-person-übersicht)
   - [Features](#multi-person-features)
   - [Konfiguration](#multi-person-konfiguration)
   - [REST-API](#multi-person-rest-api)
   - [Technische Details](#technische-details)

---

# PTZ-Steuerung

## Übersicht

Die PTZ-Tracking-Steuerung ermöglicht automatisches Schwenken und Neigen (Pan/Tilt) der Panasonic AW-HE130 Kamera, um eine Person im Bild zu zentrieren.

## PTZ Features

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

**Details:** [GSTREAMER.md](GSTREAMER.md)

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

## PTZ Konfiguration

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

# REST-API
PTZ_REST_ENABLED = True
PTZ_REST_HOST = "0.0.0.0"
PTZ_REST_PORT = 8080

# Initial-Status
PTZ_ENABLED_ON_START = False  # Startet deaktiviert
```

### Goldener Schnitt

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

## PTZ REST-API

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

## PTZ Verwendung

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

## PTZ Funktionsweise

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

### Speed-basierte Steuerung (PTS) - VERWENDET

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

## PTZ Performance

### Mit GStreamer (EMPFOHLEN)
- **Update-Rate**: 7.7 Hz (alle 130ms, Minimum laut Panasonic Spec)
- **Video-Latenz**: 30-50ms (DeckLink SDI)
- **End-to-End Latenz**: ~60-80ms (Video + Detection + PTZ)
- **Reaktionszeit**: Hervorragend für schnelle Bewegungen

### Mit FFmpeg (Fallback)
- **Update-Rate**: 7.7 Hz (alle 130ms)
- **Video-Latenz**: 100-200ms
- **End-to-End Latenz**: ~180-250ms (Video + Detection + PTZ)
- **Reaktionszeit**: Ausreichend für langsame Bewegungen

### Allgemeine Parameter
- **Minimale Bewegung**: 10 Pan/Tilt Units (vermeidet Jitter)
- **Smoothing**: Default 0.7 (70% alte Position, 30% neue Position)
- **Timeout**: 500ms pro HTTP-Request
- **Command Delay**: 130ms Mindest-Abstand zwischen Befehlen (Panasonic-Vorgabe)

## PTZ Troubleshooting

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

**Lösung 1: GStreamer verwenden** (Beste Lösung)
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

## Sicherheit

**Wichtig**: Der REST-Server hat keine Authentifizierung!

Für Produktionsumgebungen:
1. Firewall-Regeln einrichten (nur trusted IPs)
2. Reverse-Proxy mit Basic Auth (nginx)
3. VPN für Fernzugriff

---

# Multi-Person Tracking

## Multi-Person Übersicht

Das Multi-Person-Tracking-System trackt alle erkannten Personen mit persistenten IDs und erlaubt manuelle Auswahl der zu verfolgenden Person für PTZ-Steuerung.

## Multi-Person Features

- **Alle Personen tracken** - Jede Person erhält eine eindeutige Track-ID
- **Persistente IDs** - IDs bleiben über Frames hinweg erhalten
- **Manuelle Auswahl** - Wähle welche Person verfolgt werden soll
- **Loop-Funktion** - Durchschalten zwischen allen Personen
- **REST-API** - Fernsteuerung per HTTP-Endpoints
- **Visuelle Unterscheidung** - Aktive Person wird hervorgehoben

## Multi-Person Konfiguration

In `src/config.py`:

```python
# Multi-Person-Tracking aktivieren
ENABLE_MULTI_PERSON_TRACKING = True

# Maximale Distanz für Track-Zuordnung (Pixel)
MULTI_PERSON_MAX_DISTANCE = 150

# Alle Personen mit IDs anzeigen
SHOW_ALL_TRACKED_PERSONS = True

# Farben
INACTIVE_PERSON_COLOR = (100, 100, 100)  # Grau
ACTIVE_PERSON_COLOR = (0, 255, 0)        # Grün
```

## Multi-Person Verwendung

### 1. Über die Applikation

Starte die Anwendung normal:

```bash
python src/main.py
```

**Tastenkombinationen:**
- `n` - Zur nächsten Person wechseln (loop)
- `q` - Beenden
- `Space` - Pause/Resume
- `r` - Tracker zurücksetzen
- `f` - Vollbild-Toggle

### 2. Über REST-API

Die REST-API läuft standardmäßig auf `http://localhost:8090`

#### Zur nächsten Person wechseln

```bash
curl http://localhost:8090/tracking/next
```

**Response:**
```json
{
  "success": true,
  "message": "Gewechselt zu Person 2",
  "active_track_id": 2
}
```

#### Spezifische Person auswählen

```bash
curl "http://localhost:8090/tracking/select?id=1"
```

**Response:**
```json
{
  "success": true,
  "message": "Person 1 ausgewählt",
  "active_track_id": 1
}
```

#### Status aller getracken Personen

```bash
curl http://localhost:8090/tracking/status
```

**Response:**
```json
{
  "success": true,
  "tracking": {
    "total_tracks": 3,
    "active_track_id": 1,
    "tracks": [
      {
        "track_id": 1,
        "bbox": [100, 200, 400, 600],
        "center": [250, 400],
        "confidence": 0.92,
        "area": 120000,
        "frames_tracked": 145,
        "velocity": 2.3,
        "is_active": true
      },
      {
        "track_id": 2,
        "bbox": [500, 150, 700, 550],
        "center": [600, 350],
        "confidence": 0.88,
        "area": 80000,
        "frames_tracked": 98,
        "velocity": 1.1,
        "is_active": true
      }
    ]
  }
}
```

## Multi-Person REST-API

### 3. Integration mit Bitfocus Companion

Die REST-Endpoints können direkt in Companion-Buttons eingebunden werden:

**Button 1: Nächste Person**
- **Action:** HTTP Request
- **Method:** GET
- **URL:** `http://10.1.3.43:8090/tracking/next`

**Button 2: Person 1**
- **Action:** HTTP Request
- **Method:** GET
- **URL:** `http://10.1.3.43:8090/tracking/select?id=1`

**Button 3: Person 2**
- **Action:** HTTP Request
- **Method:** GET
- **URL:** `http://10.1.3.43:8090/tracking/select?id=2`

## Technische Details

### Track-ID-Vergabe

- Jede neue Person erhält eine aufsteigende ID (1, 2, 3, ...)
- IDs werden über Frames hinweg beibehalten (basierend auf Position)
- Wenn eine Person das Bild verlässt (> 30 Frames unsichtbar), wird ihre ID freigegeben

### Matching-Algorithmus

Der einfache Matching-Algorithmus funktioniert wie folgt:

1. **Distanz-basiertes Matching:** Berechne euklidische Distanz zwischen Track-Zentrum und Detection-Zentrum
2. **Schwellwert:** Nur Matches unter `MULTI_PERSON_MAX_DISTANCE` (Standard: 150px)
3. **Nearest Neighbor:** Jeder Track wird der nächstgelegenen Detection zugeordnet
4. **Neue Tracks:** Unmatched Detections werden als neue Personen erkannt

### Aktive Person

- **Auto-Select:** Bei Start wird automatisch die größte Person gewählt
- **Manuelle Auswahl:** Per API oder Tastendruck (`n`)
- **Persistenz:** Aktive Person bleibt aktiv, auch wenn sie kurz verschwindet
- **Fallback:** Wenn aktive Person verschwindet (> 30 Frames), wird automatisch größte Person gewählt

### Visualisierung

- **Grüne Box:** Aktive Person (wird von PTZ verfolgt)
- **Graue Boxen:** Alle anderen getracken Personen
- **Label:** Track-ID wird über jeder Box angezeigt
- **[ACTIVE]:** Markierung für aktive Person

## Beispielcode

Siehe `examples/multi_person_tracking_example.py` für ein vollständiges Beispiel.

```python
from src.tracking.multi_person_tracker import MultiPersonTracker

# Tracker erstellen
tracker = MultiPersonTracker(
    max_distance_threshold=150,
    smoothing_enabled=True,
    smoothing_factor=0.3
)

# Tracking aktualisieren
detections = detector.detect(frame)
active_detection = tracker.update(detections, frame.shape)

# Zur nächsten Person wechseln
new_id = tracker.select_next_person()

# Spezifische Person auswählen
success = tracker.select_person_by_id(2)

# Status aller Tracks
status = tracker.get_status()
```

## Multi-Person Troubleshooting

### Personen werden nicht erkannt

- Überprüfe `CONFIDENCE_THRESHOLD` in config.py
- Erhöhe `MULTI_PERSON_MAX_DISTANCE` wenn Personen sich schnell bewegen

### IDs springen/wechseln häufig

- Erhöhe `MULTI_PERSON_MAX_DISTANCE` für besseres Matching
- Reduziere `MAX_FRAMES_WITHOUT_DETECTION` um Tracks länger zu halten

### REST-API antwortet nicht

- Überprüfe ob REST-Server gestartet ist (log-Ausgabe)
- Prüfe Port-Verfügbarkeit: `lsof -i :8090`
- Firewall-Einstellungen überprüfen

## Migration von Single-Person-Tracking

Um von Single-Person- auf Multi-Person-Tracking umzustellen:

1. **Config anpassen:**
   ```python
   ENABLE_MULTI_PERSON_TRACKING = True
   ```

2. **Anwendung neu starten**

Das war's! Die Anwendung verwendet automatisch den MultiPersonTracker.

Um zurückzuwechseln:
```python
ENABLE_MULTI_PERSON_TRACKING = False
```

## Performance

- **CPU-Impact:** ~5-10% höher als Single-Person-Tracking
- **Memory:** Pro getrackter Person ~1-2 KB
- **Empfohlen:** Max. 5-10 gleichzeitige Personen für beste Performance
