# Multi-Person Tracking

## Überblick

Das Multi-Person-Tracking-System trackt alle erkannten Personen mit persistenten IDs und erlaubt manuelle Auswahl der zu verfolgenden Person für PTZ-Steuerung.

## Features

- **Alle Personen tracken** - Jede Person erhält eine eindeutige Track-ID
- **Persistente IDs** - IDs bleiben über Frames hinweg erhalten
- **Manuelle Auswahl** - Wähle welche Person verfolgt werden soll
- **Loop-Funktion** - Durchschalten zwischen allen Personen
- **REST-API** - Fernsteuerung per HTTP-Endpoints
- **Visuelle Unterscheidung** - Aktive Person wird hervorgehoben

## Konfiguration

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

## Verwendung

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

## Troubleshooting

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

## Weiterführende Links

- [PTZ Control Documentation](PTZ_CONTROL.md)
- [REST API Documentation](../README.md#rest-api)
- [Configuration Reference](../src/config.py)
