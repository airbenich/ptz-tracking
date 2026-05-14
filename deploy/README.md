# PTZ Tracking - Service Deployment

Dieses Verzeichnis enthält alle Dateien für die Installation und Verwaltung von PTZ Tracking als System-Service.

## 📁 Verzeichnisstruktur

```
deploy/
├── systemd/                    # Linux systemd Service-Files
│   └── ptz-tracking.service
├── launchd/                    # macOS launchd plist-Files
│   └── com.ptztracking.service.plist
├── logrotate/                  # Log-Rotation Konfiguration
│   └── ptz-tracking
├── scripts/                    # Installation und Management Scripts
│   ├── install-linux.sh        # Linux Installation
│   ├── install-macos.sh        # macOS Installation
│   ├── uninstall-linux.sh      # Linux Deinstallation
│   ├── uninstall-macos.sh      # macOS Deinstallation
│   ├── service-manager.sh      # Service Management Tool
│   └── health-check.py         # Health-Check Script
└── README.md                   # Diese Datei
```

## 🚀 Installation

### Linux (systemd)

```bash
# 1. Als root ausführen
sudo ./deploy/scripts/install-linux.sh

# 2. Konfiguration anpassen (optional)
sudo nano /opt/ptz-tracking/src/config.py

# 3. Service aktivieren und starten
sudo systemctl enable ptz-tracking
sudo systemctl start ptz-tracking

# 4. Status prüfen
sudo systemctl status ptz-tracking
```

**Installationspfad:** `/opt/ptz-tracking`

### macOS (launchd)

```bash
# 1. Als root ausführen
sudo ./deploy/scripts/install-macos.sh

# 2. Konfiguration anpassen (optional)
sudo nano /usr/local/opt/ptz-tracking/src/config.py

# 3. Service laden und starten
sudo launchctl load /Library/LaunchDaemons/com.ptztracking.service.plist
sudo launchctl start com.ptztracking.service

# 4. Status prüfen
sudo launchctl list | grep ptztracking
```

**Installationspfad:** `/usr/local/opt/ptz-tracking`

## 🛠️ Service-Verwaltung

### Mit Service-Manager (empfohlen)

Das `service-manager.sh` Script vereinfacht die Service-Verwaltung auf beiden Plattformen:

```bash
# Service starten
./deploy/scripts/service-manager.sh start

# Service stoppen
./deploy/scripts/service-manager.sh stop

# Service neu starten
./deploy/scripts/service-manager.sh restart

# Status anzeigen
./deploy/scripts/service-manager.sh status

# Live-Logs anzeigen
./deploy/scripts/service-manager.sh logs

# Nur Fehler anzeigen
./deploy/scripts/service-manager.sh logs-error

# Health-Check
./deploy/scripts/service-manager.sh health

# Autostart aktivieren/deaktivieren
./deploy/scripts/service-manager.sh enable
./deploy/scripts/service-manager.sh disable
```

### Manuelle Verwaltung

#### Linux (systemd)

```bash
# Starten/Stoppen/Neu starten
sudo systemctl start ptz-tracking
sudo systemctl stop ptz-tracking
sudo systemctl restart ptz-tracking

# Status
sudo systemctl status ptz-tracking

# Logs (live)
sudo journalctl -u ptz-tracking -f

# Logs (letzte 100 Zeilen)
sudo journalctl -u ptz-tracking -n 100

# Autostart
sudo systemctl enable ptz-tracking   # aktivieren
sudo systemctl disable ptz-tracking  # deaktivieren
```

#### macOS (launchd)

```bash
# Starten/Stoppen
sudo launchctl start com.ptztracking.service
sudo launchctl stop com.ptztracking.service

# Status
sudo launchctl list | grep ptztracking

# Logs (live)
tail -f /usr/local/opt/ptz-tracking/logs/*.log

# Service laden/entladen
sudo launchctl load /Library/LaunchDaemons/com.ptztracking.service.plist
sudo launchctl unload /Library/LaunchDaemons/com.ptztracking.service.plist
```

## 🔍 Health-Checks

Das Health-Check Script prüft:
- ✅ Ob der Prozess läuft
- ✅ Ob Log-Dateien aktualisiert werden
- ✅ Fehlerrate in Logs
- ✅ Verfügbarer Disk-Space

```bash
# Manuell ausführen
python3 deploy/scripts/health-check.py

# Mit Service-Manager
./deploy/scripts/service-manager.sh health

# Exit-Codes:
# 0 = OK: Alles funktioniert
# 1 = WARNING: Kleinere Probleme
# 2 = CRITICAL: Schwerwiegende Probleme
# 3 = UNKNOWN: Check-Fehler
```

### Automatische Health-Checks (cron)

**Linux (crontab):**

```bash
# Füge zu /etc/crontab hinzu:
*/5 * * * * root /opt/ptz-tracking/deploy/scripts/health-check.py >> /var/log/ptz-health.log 2>&1
```

**macOS (launchd):**

Erstelle `/Library/LaunchDaemons/com.ptztracking.healthcheck.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ptztracking.healthcheck</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/usr/local/opt/ptz-tracking/deploy/scripts/health-check.py</string>
    </array>
    <key>StartInterval</key>
    <integer>300</integer>
    <key>StandardOutPath</key>
    <string>/var/log/ptz-health.log</string>
</dict>
</plist>
```

## 📝 Log-Management

### Linux (logrotate)

Die Log-Rotation wird automatisch konfiguriert:

```bash
# Installation (bereits im install-linux.sh enthalten)
sudo cp deploy/logrotate/ptz-tracking /etc/logrotate.d/

# Manuell testen
sudo logrotate -f /etc/logrotate.d/ptz-tracking

# Konfiguration:
# - Täglich rotieren
# - 30 Tage aufbewahren
# - Komprimieren
# - Max 100MB pro Datei
```

### macOS

Logs werden in `/usr/local/opt/ptz-tracking/logs/` gespeichert.

Manuelle Rotation:

```bash
# Alte Logs archivieren
cd /usr/local/opt/ptz-tracking/logs
gzip *.log.1 2>/dev/null || true

# Logs älter als 30 Tage löschen
find . -name "*.log.gz" -mtime +30 -delete
```

## 🗑️ Deinstallation

### Linux

```bash
sudo ./deploy/scripts/uninstall-linux.sh
```

### macOS

```bash
sudo ./deploy/scripts/uninstall-macos.sh
```

## ⚙️ Konfiguration

### Service-Konfiguration

**Linux (`/etc/systemd/system/ptz-tracking.service`):**

Wichtige Parameter:
- `User/Group`: Service-User (Standard: ptztracking)
- `WorkingDirectory`: Installationsverzeichnis
- `Restart`: Restart-Strategie (on-failure)
- `RestartSec`: Wartezeit vor Restart (10s)
- `MemoryLimit`: Speicher-Limit (2GB)

Nach Änderungen:
```bash
sudo systemctl daemon-reload
sudo systemctl restart ptz-tracking
```

**macOS (`/Library/LaunchDaemons/com.ptztracking.service.plist`):**

Wichtige Parameter:
- `UserName`: Service-User
- `RunAtLoad`: Bei Boot starten (true/false)
- `KeepAlive`: Auto-Restart bei Crash
- `ThrottleInterval`: Restart-Verzögerung (10s)

Nach Änderungen:
```bash
sudo launchctl unload /Library/LaunchDaemons/com.ptztracking.service.plist
sudo launchctl load /Library/LaunchDaemons/com.ptztracking.service.plist
```

### Anwendungs-Konfiguration

Bearbeite die `config.py`:

**Linux:**
```bash
sudo nano /opt/ptz-tracking/src/config.py
```

**macOS:**
```bash
sudo nano /usr/local/opt/ptz-tracking/src/config.py
```

Wichtige Einstellungen:
- `VIDEO_SOURCE`: "ffmpeg", "webcam", "file"
- `FFMPEG_INPUT_DEVICE`: Device-Name
- `HEADLESS_MODE`: Muss `True` sein für Service
- `LOG_TO_FILE`: Empfohlen: `True`

Nach Änderungen Service neu starten.

## 🔒 Sicherheit

### Berechtigungen

- Service läuft unter dediziertem User (Linux: `ptztracking`)
- Nur Lese-Zugriff auf Anwendungsdateien
- Schreib-Zugriff nur auf `logs/` und `output/`

### Systemd-Härtung (Linux)

Die Service-Datei enthält Security-Features:
- `NoNewPrivileges=true`: Verhindert Privilege Escalation
- `PrivateTmp=true`: Isoliertes /tmp
- `ProtectSystem=strict`: Read-Only System-Verzeichnisse
- `ProtectHome=true`: Kein Zugriff auf Home-Verzeichnisse

## 📊 Monitoring

### Systemd Journal (Linux)

```bash
# Fehler der letzten Stunde
sudo journalctl -u ptz-tracking --since "1 hour ago" -p err

# Performance-Statistiken
sudo systemctl show ptz-tracking

# Resource-Usage
sudo systemd-cgtop
```

### Log-Analyse

```bash
# Fehlerrate
grep -c ERROR /opt/ptz-tracking/logs/*.log

# Letzte Fehler
tail -100 /opt/ptz-tracking/logs/*.log | grep ERROR

# FPS-Performance
grep "FPS:" /opt/ptz-tracking/logs/*.log | tail -20
```

## 🐛 Troubleshooting

### Service startet nicht

```bash
# 1. Detaillierte Logs prüfen
sudo journalctl -u ptz-tracking -n 100 --no-pager

# 2. Manuell testen
cd /opt/ptz-tracking
source venv/bin/activate
python src/main.py --headless --debug

# 3. Berechtigungen prüfen
ls -la /opt/ptz-tracking

# 4. Dependencies prüfen
source venv/bin/activate
pip list
```

### Service crasht wiederholt

```bash
# Health-Check ausführen
./deploy/scripts/service-manager.sh health

# Fehler-Logs prüfen
./deploy/scripts/service-manager.sh logs-error

# Restart-Counter prüfen (systemd)
sudo systemctl show ptz-tracking | grep NRestarts
```

### Video-Input Probleme

```bash
# FFmpeg-Devices auflisten
ffmpeg -f avfoundation -list_devices true -i ""  # macOS
ffmpeg -f v4l2 -list_devices true -i ""          # Linux

# Webcam-Berechtigungen (macOS)
# Systemeinstellungen → Datenschutz & Sicherheit → Kamera
```

## 📚 Weitere Ressourcen

- [systemd Documentation](https://www.freedesktop.org/software/systemd/man/)
- [launchd Documentation](https://www.launchd.info/)
- [PTZ Tracking Main README](../README.md)
- [Project Specification](../PROJECT_SPECIFICATION.md)
