#!/bin/bash
#
# PTZ Tracking - launchd Service Installation (macOS)
#

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Konfiguration
SERVICE_NAME="com.ptztracking.service"
INSTALL_DIR="/usr/local/opt/ptz-tracking"
PLIST_FILE="deploy/launchd/com.ptztracking.service.plist"
SERVICE_USER="ptztracking"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}PTZ Tracking - Service Installation${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Root-Rechte prüfen
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Bitte als root ausführen (sudo)${NC}"
    exit 1
fi

# macOS-Check
if [ "$(uname)" != "Darwin" ]; then
    echo -e "${RED}Dieses Script ist nur für macOS${NC}"
    exit 1
fi

# Schritt 1: Service-User erstellen (optional auf macOS)
echo -e "${YELLOW}[1/7] Service-User...${NC}"
echo -e "${YELLOW}Hinweis: Auf macOS wird der aktuelle User verwendet${NC}"
echo -e "${GREEN}✓ User-Konfiguration übersprungen${NC}"

# Schritt 2: Installationsverzeichnis erstellen
echo -e "\n${YELLOW}[2/7] Erstelle Installationsverzeichnis...${NC}"
mkdir -p "$INSTALL_DIR"
echo -e "${GREEN}✓ Verzeichnis erstellt: $INSTALL_DIR${NC}"

# Schritt 3: Dateien kopieren
echo -e "\n${YELLOW}[3/7] Kopiere Anwendungsdateien...${NC}"
cp -r src "$INSTALL_DIR/"
cp -r models "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"
echo -e "${GREEN}✓ Dateien kopiert${NC}"

# Schritt 4: Virtual Environment erstellen
echo -e "\n${YELLOW}[4/7] Erstelle Virtual Environment...${NC}"
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
echo -e "${GREEN}✓ Virtual Environment erstellt${NC}"

# Schritt 5: Verzeichnisse für Logs und Output
echo -e "\n${YELLOW}[5/7] Erstelle Log-Verzeichnisse...${NC}"
mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$INSTALL_DIR/output"
echo -e "${GREEN}✓ Verzeichnisse erstellt${NC}"

# Schritt 6: Berechtigungen setzen
echo -e "\n${YELLOW}[6/7] Setze Berechtigungen...${NC}"
chown -R "$(logname):staff" "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"
chmod -R 777 "$INSTALL_DIR/logs"
chmod -R 777 "$INSTALL_DIR/output"
echo -e "${GREEN}✓ Berechtigungen gesetzt${NC}"

# Schritt 7: launchd Service installieren
echo -e "\n${YELLOW}[7/7] Installiere launchd Service...${NC}"

# plist anpassen (User ersetzen)
CURRENT_USER=$(logname)
sed "s/ptztracking/$CURRENT_USER/g" "$(dirname "$0")/../launchd/com.ptztracking.service.plist" > "/Library/LaunchDaemons/$SERVICE_NAME.plist"

# Berechtigungen für plist
chown root:wheel "/Library/LaunchDaemons/$SERVICE_NAME.plist"
chmod 644 "/Library/LaunchDaemons/$SERVICE_NAME.plist"

echo -e "${GREEN}✓ Service installiert${NC}"

# Abschluss
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Installation abgeschlossen!${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo -e "Nächste Schritte:"
echo -e "  ${YELLOW}1.${NC} Konfiguration anpassen: $INSTALL_DIR/src/config.py"
echo -e "  ${YELLOW}2.${NC} Service laden: sudo launchctl load /Library/LaunchDaemons/$SERVICE_NAME.plist"
echo -e "  ${YELLOW}3.${NC} Service starten: sudo launchctl start $SERVICE_NAME"
echo -e "  ${YELLOW}4.${NC} Status prüfen: sudo launchctl list | grep ptztracking"
echo -e "  ${YELLOW}5.${NC} Logs anzeigen: tail -f $INSTALL_DIR/logs/stdout.log\n"

echo -e "${YELLOW}Service beenden:${NC}"
echo -e "  sudo launchctl stop $SERVICE_NAME"
echo -e "  sudo launchctl unload /Library/LaunchDaemons/$SERVICE_NAME.plist\n"

echo -e "${YELLOW}Hinweis:${NC} Service läuft im Headless-Modus (ohne Display)"
echo -e "${YELLOW}Tipp:${NC} Für Tests verwende: python src/main.py --source webcam\n"
