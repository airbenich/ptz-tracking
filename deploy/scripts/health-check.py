#!/usr/bin/env python3
"""
PTZ Tracking - Health Check Script
Prüft ob Service läuft und funktioniert
"""

import sys
import os
import time
import subprocess
from pathlib import Path

# Exit Codes
EXIT_OK = 0
EXIT_WARNING = 1
EXIT_CRITICAL = 2
EXIT_UNKNOWN = 3


def check_process_running(process_name="python"):
    """Prüft ob PTZ Tracking Prozess läuft"""
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'ptz.*tracking'],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"UNKNOWN: Fehler bei Prozess-Check: {e}")
        return False


def check_log_file(log_dir="/opt/ptz-tracking/logs"):
    """Prüft ob Log-Dateien aktualisiert werden"""
    try:
        log_dir = Path(log_dir)
        
        # Finde neueste Log-Datei
        log_files = list(log_dir.glob("*.log"))
        if not log_files:
            print("WARNING: Keine Log-Dateien gefunden")
            return False
        
        newest_log = max(log_files, key=lambda p: p.stat().st_mtime)
        
        # Prüfe ob Log-Datei in letzten 5 Minuten aktualisiert wurde
        age = time.time() - newest_log.stat().st_mtime
        
        if age > 300:  # 5 Minuten
            print(f"WARNING: Log-Datei nicht aktualisiert seit {age:.0f}s")
            return False
        
        return True
        
    except Exception as e:
        print(f"UNKNOWN: Fehler bei Log-Check: {e}")
        return False


def check_error_rate(log_dir="/opt/ptz-tracking/logs", threshold=10):
    """Prüft Fehlerrate in Logs"""
    try:
        log_dir = Path(log_dir)
        
        # Finde neueste Log-Datei
        log_files = list(log_dir.glob("*.log"))
        if not log_files:
            return True  # Keine Logs = kein Problem (noch)
        
        newest_log = max(log_files, key=lambda p: p.stat().st_mtime)
        
        # Zähle ERROR-Zeilen in letzten 1000 Zeilen
        result = subprocess.run(
            ['tail', '-n', '1000', str(newest_log)],
            capture_output=True,
            text=True
        )
        
        error_count = result.stdout.count('ERROR')
        
        if error_count > threshold:
            print(f"WARNING: Hohe Fehlerrate: {error_count} Fehler in letzten 1000 Zeilen")
            return False
        
        return True
        
    except Exception as e:
        print(f"UNKNOWN: Fehler bei Error-Rate-Check: {e}")
        return True  # Bei Fehler nicht warnen


def check_disk_space(path="/opt/ptz-tracking", threshold_percent=90):
    """Prüft verfügbaren Disk-Space"""
    try:
        result = subprocess.run(
            ['df', '-h', path],
            capture_output=True,
            text=True
        )
        
        # Parse df output
        lines = result.stdout.strip().split('\n')
        if len(lines) < 2:
            return True
        
        # Zweite Zeile enthält die Daten
        fields = lines[1].split()
        use_percent = int(fields[4].rstrip('%'))
        
        if use_percent > threshold_percent:
            print(f"WARNING: Disk-Space kritisch: {use_percent}% belegt")
            return False
        
        return True
        
    except Exception as e:
        print(f"UNKNOWN: Fehler bei Disk-Space-Check: {e}")
        return True


def main():
    """Hauptfunktion"""
    checks = {
        'Prozess läuft': check_process_running(),
        'Log-Datei aktuell': check_log_file(),
        'Fehlerrate OK': check_error_rate(),
        'Disk-Space OK': check_disk_space()
    }
    
    # Ergebnisse zusammenfassen
    all_ok = all(checks.values())
    failed_checks = [name for name, result in checks.items() if not result]
    
    if all_ok:
        print(f"OK: Alle Checks bestanden ({len(checks)}/{len(checks)})")
        return EXIT_OK
    
    elif len(failed_checks) == len(checks):
        print(f"CRITICAL: Alle Checks fehlgeschlagen: {', '.join(failed_checks)}")
        return EXIT_CRITICAL
    
    else:
        print(f"WARNING: Einige Checks fehlgeschlagen: {', '.join(failed_checks)}")
        print(f"Details: {len(checks) - len(failed_checks)}/{len(checks)} Checks OK")
        return EXIT_WARNING


if __name__ == "__main__":
    sys.exit(main())
