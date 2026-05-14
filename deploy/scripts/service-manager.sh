#!/bin/bash
#
# PTZ Tracking - Service Management Script
# Vereinfachte Verwaltung des PTZ Tracking Service
#

set -e

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Konfiguration
SERVICE_NAME="ptz-tracking"
INSTALL_DIR="/opt/ptz-tracking"
LOG_DIR="$INSTALL_DIR/logs"

# Plattform erkennen
if [ "$(uname)" == "Darwin" ]; then
    PLATFORM="macos"
    SERVICE_NAME="com.ptztracking.service"
else
    PLATFORM="linux"
fi

# Hilfe
show_help() {
    echo -e "${BLUE}PTZ Tracking - Service Management${NC}\n"
    echo "Verwendung: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start       - Service starten"
    echo "  stop        - Service stoppen"
    echo "  restart     - Service neu starten"
    echo "  status      - Service-Status anzeigen"
    echo "  logs        - Live-Logs anzeigen"
    echo "  logs-error  - Nur Fehler anzeigen"
    echo "  health      - Health-Check durchführen"
    echo "  enable      - Service beim Boot aktivieren"
    echo "  disable     - Service beim Boot deaktivieren"
    echo ""
}

# Start
cmd_start() {
    echo -e "${YELLOW}Starte PTZ Tracking...${NC}"
    
    if [ "$PLATFORM" == "macos" ]; then
        sudo launchctl start "$SERVICE_NAME"
    else
        sudo systemctl start "$SERVICE_NAME"
    fi
    
    sleep 2
    cmd_status
}

# Stop
cmd_stop() {
    echo -e "${YELLOW}Stoppe PTZ Tracking...${NC}"
    
    if [ "$PLATFORM" == "macos" ]; then
        sudo launchctl stop "$SERVICE_NAME"
    else
        sudo systemctl stop "$SERVICE_NAME"
    fi
    
    echo -e "${GREEN}✓ Service gestoppt${NC}"
}

# Restart
cmd_restart() {
    echo -e "${YELLOW}Starte PTZ Tracking neu...${NC}"
    
    if [ "$PLATFORM" == "macos" ]; then
        sudo launchctl stop "$SERVICE_NAME" 2>/dev/null || true
        sleep 1
        sudo launchctl start "$SERVICE_NAME"
    else
        sudo systemctl restart "$SERVICE_NAME"
    fi
    
    sleep 2
    cmd_status
}

# Status
cmd_status() {
    echo -e "${BLUE}PTZ Tracking Status:${NC}\n"
    
    if [ "$PLATFORM" == "macos" ]; then
        if sudo launchctl list | grep -q "$SERVICE_NAME"; then
            echo -e "${GREEN}✓ Service läuft${NC}"
            sudo launchctl list | grep "$SERVICE_NAME"
        else
            echo -e "${RED}✗ Service läuft nicht${NC}"
        fi
    else
        sudo systemctl status "$SERVICE_NAME" --no-pager || true
    fi
}

# Logs
cmd_logs() {
    echo -e "${BLUE}PTZ Tracking Logs (Ctrl+C zum Beenden):${NC}\n"
    
    if [ "$PLATFORM" == "macos" ]; then
        tail -f "$LOG_DIR"/*.log
    else
        sudo journalctl -u "$SERVICE_NAME" -f
    fi
}

# Error Logs
cmd_logs_error() {
    echo -e "${RED}PTZ Tracking Fehler (letzte 50 Zeilen):${NC}\n"
    
    if [ "$PLATFORM" == "macos" ]; then
        grep -i error "$LOG_DIR"/*.log | tail -50
    else
        sudo journalctl -u "$SERVICE_NAME" -p err -n 50 --no-pager
    fi
}

# Health Check
cmd_health() {
    echo -e "${BLUE}PTZ Tracking Health Check:${NC}\n"
    
    if [ -f "$INSTALL_DIR/deploy/scripts/health-check.py" ]; then
        python3 "$INSTALL_DIR/deploy/scripts/health-check.py"
    else
        echo -e "${YELLOW}Health-Check Script nicht gefunden${NC}"
        echo "Einfacher Status-Check:"
        
        if pgrep -f "ptz.*tracking" > /dev/null; then
            echo -e "${GREEN}✓ Prozess läuft${NC}"
        else
            echo -e "${RED}✗ Prozess läuft nicht${NC}"
        fi
    fi
}

# Enable
cmd_enable() {
    echo -e "${YELLOW}Aktiviere PTZ Tracking beim Boot...${NC}"
    
    if [ "$PLATFORM" == "macos" ]; then
        # Auf macOS automatisch beim Load aktiviert
        echo -e "${GREEN}✓ Service ist aktiviert (RunAtLoad=true)${NC}"
    else
        sudo systemctl enable "$SERVICE_NAME"
        echo -e "${GREEN}✓ Service aktiviert${NC}"
    fi
}

# Disable
cmd_disable() {
    echo -e "${YELLOW}Deaktiviere PTZ Tracking beim Boot...${NC}"
    
    if [ "$PLATFORM" == "macos" ]; then
        echo -e "${YELLOW}Auf macOS: plist-File bearbeiten und RunAtLoad=false setzen${NC}"
    else
        sudo systemctl disable "$SERVICE_NAME"
        echo -e "${GREEN}✓ Service deaktiviert${NC}"
    fi
}

# Main
case "$1" in
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    status)
        cmd_status
        ;;
    logs)
        cmd_logs
        ;;
    logs-error)
        cmd_logs_error
        ;;
    health)
        cmd_health
        ;;
    enable)
        cmd_enable
        ;;
    disable)
        cmd_disable
        ;;
    *)
        show_help
        exit 1
        ;;
esac
