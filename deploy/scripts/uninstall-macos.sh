#!/bin/bash
#
# PTZ Tracking - Service Deinstallation (macOS)
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SERVICE_NAME="com.ptztracking.service"
INSTALL_DIR="/usr/local/opt/ptz-tracking"
PLIST_PATH="/Library/LaunchDaemons/$SERVICE_NAME.plist"

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

# Service stoppen und entladen
echo -e "\n${YELLOW}[1/3] Stoppe Service...${NC}"
if launchctl list | grep -q "$SERVICE_NAME"; then
    launchctl stop "$SERVICE_NAME" 2>/dev/null || true
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    echo -e "${GREEN}✓ Service gestoppt und entladen${NC}"
else
    echo -e "${GREEN}✓ Service ist nicht geladen${NC}"
fi

# plist-File entfernen
echo -e "\n${YELLOW}[2/3] Entferne Service-File...${NC}"
if [ -f "$PLIST_PATH" ]; then
    rm "$PLIST_PATH"
    echo -e "${GREEN}✓ plist-File entfernt${NC}"
fi

# Installationsverzeichnis entfernen
echo -e "\n${YELLOW}[3/3] Entferne Installationsverzeichnis...${NC}"
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

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deinstallation abgeschlossen!${NC}"
echo -e "${GREEN}========================================${NC}\n"
