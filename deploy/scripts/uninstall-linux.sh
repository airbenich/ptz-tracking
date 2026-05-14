#!/bin/bash
#
# PTZ Tracking - Service Deinstallation (Linux)
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SERVICE_NAME="ptz-tracking"
INSTALL_DIR="/opt/ptz-tracking"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}PTZ Tracking - Service Deinstallation${NC}"
echo -e "${YELLOW}========================================${NC}\n"

# Root-Rechte prüfen
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Bitte als root ausführen (sudo)${NC}"
    exit 1
fi

# Bestätigung
read -p "Möchten Sie PTZ Tracking wirklich deinstallieren? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Abgebrochen${NC}"
    exit 0
fi

# Service stoppen und deaktivieren
echo -e "\n${YELLOW}[1/4] Stoppe Service...${NC}"
if systemctl is-active --quiet "$SERVICE_NAME"; then
    systemctl stop "$SERVICE_NAME"
    echo -e "${GREEN}✓ Service gestoppt${NC}"
else
    echo -e "${GREEN}✓ Service ist nicht aktiv${NC}"
fi

if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    systemctl disable "$SERVICE_NAME"
    echo -e "${GREEN}✓ Service deaktiviert${NC}"
fi

# Service-File entfernen
echo -e "\n${YELLOW}[2/4] Entferne Service-File...${NC}"
if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
    rm "/etc/systemd/system/$SERVICE_NAME.service"
    systemctl daemon-reload
    echo -e "${GREEN}✓ Service-File entfernt${NC}"
fi

# Installationsverzeichnis entfernen
echo -e "\n${YELLOW}[3/4] Entferne Installationsverzeichnis...${NC}"
read -p "Logs und Output-Dateien auch löschen? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$INSTALL_DIR"
    echo -e "${GREEN}✓ Alles entfernt${NC}"
else
    # Nur Anwendung entfernen, Logs behalten
    rm -rf "$INSTALL_DIR/src"
    rm -rf "$INSTALL_DIR/models"
    rm -rf "$INSTALL_DIR/venv"
    rm -f "$INSTALL_DIR/requirements.txt"
    echo -e "${GREEN}✓ Anwendung entfernt, Logs beibehalten in: $INSTALL_DIR/logs${NC}"
fi

# Service-User entfernen (optional)
echo -e "\n${YELLOW}[4/4] Service-User...${NC}"
read -p "Service-User 'ptztracking' auch löschen? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if id "ptztracking" &>/dev/null; then
        userdel ptztracking
        echo -e "${GREEN}✓ User entfernt${NC}"
    fi
else
    echo -e "${YELLOW}✓ User beibehalten${NC}"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deinstallation abgeschlossen!${NC}"
echo -e "${GREEN}========================================${NC}\n"
