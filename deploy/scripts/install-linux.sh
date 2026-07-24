#!/bin/bash
#
# PTZ Tracking - systemd Service Installation (Linux)
#

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Konfiguration
SERVICE_NAME="ptz-tracking"
INSTALL_DIR="/opt/ptz-tracking"
SERVICE_FILE="deploy/systemd/ptz-tracking.service"
SERVICE_USER="ptztracking"
SERVICE_GROUP="ptztracking"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}PTZ Tracking - Service Installation${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Root-Rechte prüfen
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Bitte als root ausführen (sudo)${NC}"
    exit 1
fi

# System-Check
if ! command -v systemctl &> /dev/null; then
    echo -e "${RED}systemd ist nicht verfügbar${NC}"
    echo -e "${YELLOW}Dieses Script ist nur für systemd-basierte Linux-Distributionen${NC}"
    exit 1
fi

# Schritt 1: Service-User erstellen
echo -e "${YELLOW}[1/7] Erstelle Service-User...${NC}"
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd --system --no-create-home --shell /bin/false "$SERVICE_USER"
    echo -e "${GREEN}✓ User '$SERVICE_USER' erstellt${NC}"
else
    echo -e "${GREEN}✓ User '$SERVICE_USER' existiert bereits${NC}"
fi

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

# Schritt 4: GStreamer-Check (optional aber empfohlen)
echo -e "\n${YELLOW}[4/8] Prüfe GStreamer-Installation...${NC}"
if command -v gst-launch-1.0 &> /dev/null; then
    echo -e "${GREEN}✓ GStreamer bereits installiert${NC}"
else
    echo -e "${YELLOW}⚠️  GStreamer nicht gefunden${NC}"
    echo -e "${YELLOW}GStreamer wird für optimale Performance empfohlen (70% niedrigere Latenz)${NC}"
    echo -e "${YELLOW}Installation: ./install-gstreamer.sh im Projekt-Root${NC}"
    echo -e "${YELLOW}Oder manuell: apt-get install python3-gi gstreamer1.0-tools gstreamer1.0-plugins-*${NC}"
fi

# Schritt 5: Virtual Environment erstellen
echo -e "\n${YELLOW}[5/8] Erstelle Virtual Environment...${NC}"
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
echo -e "${GREEN}✓ Virtual Environment erstellt${NC}"

# Schritt 6: Verzeichnisse für Logs und Output
echo -e "\n${YELLOW}[6/8] Erstelle Log-Verzeichnisse...${NC}"
mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$INSTALL_DIR/output"
echo -e "${GREEN}✓ Verzeichnisse erstellt${NC}"

# Schritt 7: Berechtigungen setzen
echo -e "\n${YELLOW}[7/8] Setze Berechtigungen...${NC}"
chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"
chmod -R 777 "$INSTALL_DIR/logs"
chmod -R 777 "$INSTALL_DIR/output"
echo -e "${GREEN}✓ Berechtigungen gesetzt${NC}"

# Schritt 8: systemd Service installieren
echo -e "\n${YELLOW}[8/8] Installiere systemd Service...${NC}"
cp "$(dirname "$0")/../systemd/ptz-tracking.service" /etc/systemd/system/
systemctl daemon-reload
echo -e "${GREEN}✓ Service installiert${NC}"

# Abschluss
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Installation abgeschlossen!${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo -e "Nächste Schritte:"
echo -e "  ${YELLOW}1.${NC} GStreamer installieren (EMPFOHLEN): ./install-gstreamer.sh"
echo -e "  ${YELLOW}2.${NC} Konfiguration anpassen: $INSTALL_DIR/src/config.py"
echo -e "       → VIDEO_SOURCE = 'gstreamer' (empfohlen) oder 'ffmpeg'"
echo -e "  ${YELLOW}3.${NC} Service aktivieren: sudo systemctl enable $SERVICE_NAME"
echo -e "  ${YELLOW}4.${NC} Service starten: sudo systemctl start $SERVICE_NAME"
echo -e "  ${YELLOW}5.${NC} Status prüfen: sudo systemctl status $SERVICE_NAME"
echo -e "  ${YELLOW}6.${NC} Logs anzeigen: sudo journalctl -u $SERVICE_NAME -f\n"

echo -e "${YELLOW}Hinweis:${NC} Service läuft im Headless-Modus (ohne Display)"
echo -e "${YELLOW}Tipp:${NC} Für Tests verwende: python src/main.py --source webcam\n"
