#!/bin/bash
#
# GStreamer Installation Script für PTZ Tracking
# Installiert alle notwendigen GStreamer-Komponenten
#
# Usage:
#   chmod +x install-gstreamer.sh
#   ./install-gstreamer.sh
#

set -e  # Exit bei Fehler

echo "=================================================="
echo "GStreamer Installation für PTZ Tracking"
echo "=================================================="
echo ""

# Betriebssystem erkennen
OS="$(uname -s)"
case "${OS}" in
    Darwin*)
        PLATFORM="macOS"
        ;;
    Linux*)
        PLATFORM="Linux"
        ;;
    *)
        echo "❌ Nicht unterstütztes Betriebssystem: ${OS}"
        exit 1
        ;;
esac

echo "Erkanntes System: ${PLATFORM}"
echo ""

# macOS Installation
if [ "${PLATFORM}" = "macOS" ]; then
    echo "🍺 Installiere GStreamer via Homebrew..."
    echo ""
    
    # Prüfe ob Homebrew installiert ist
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew ist nicht installiert!"
        echo "Installation: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    echo "📦 Installiere GStreamer-Pakete..."
    brew install gstreamer gst-python gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly
    
    echo ""
    echo "✅ GStreamer erfolgreich installiert!"
    echo ""
    echo "⚠️  Blackmagic DeckLink Support:"
    echo "   1. Download Desktop Video SDK: https://www.blackmagicdesign.com/support/"
    echo "   2. Installiere Desktop Video Driver"
    echo "   3. decklinkvideosrc Plugin wird automatisch erkannt"
    echo ""

# Linux Installation
elif [ "${PLATFORM}" = "Linux" ]; then
    echo "🐧 Installiere GStreamer für Linux..."
    echo ""
    
    # Prüfe Linux-Distribution
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
    else
        echo "❌ Kann Linux-Distribution nicht erkennen"
        exit 1
    fi
    
    case "${DISTRO}" in
        ubuntu|debian)
            echo "📦 Installiere GStreamer-Pakete (Ubuntu/Debian)..."
            sudo apt-get update
            sudo apt-get install -y \
                python3-gi \
                gstreamer1.0-tools \
                gstreamer1.0-plugins-base \
                gstreamer1.0-plugins-good \
                gstreamer1.0-plugins-bad \
                gstreamer1.0-plugins-ugly \
                gstreamer1.0-libav
            
            echo ""
            echo "📦 Installiere Blackmagic DeckLink Support..."
            sudo apt-get install -y gstreamer1.0-decklink || echo "⚠️  DeckLink Plugin nicht verfügbar (manuell installieren)"
            
            echo ""
            echo "✅ GStreamer erfolgreich installiert!"
            ;;
        
        fedora|centos|rhel)
            echo "📦 Installiere GStreamer-Pakete (Fedora/RHEL)..."
            sudo dnf install -y \
                python3-gobject \
                gstreamer1 \
                gstreamer1-plugins-base \
                gstreamer1-plugins-good \
                gstreamer1-plugins-bad-free \
                gstreamer1-plugins-ugly-free
            
            echo ""
            echo "✅ GStreamer erfolgreich installiert!"
            echo "⚠️  DeckLink-Support muss manuell installiert werden"
            ;;
        
        arch)
            echo "📦 Installiere GStreamer-Pakete (Arch Linux)..."
            sudo pacman -S --noconfirm \
                python-gobject \
                gstreamer \
                gst-plugins-base \
                gst-plugins-good \
                gst-plugins-bad \
                gst-plugins-ugly
            
            echo ""
            echo "✅ GStreamer erfolgreich installiert!"
            ;;
        
        *)
            echo "❌ Nicht unterstützte Linux-Distribution: ${DISTRO}"
            echo "Bitte installiere GStreamer manuell:"
            echo "  - python3-gi oder python-gobject"
            echo "  - gstreamer1.0-* Pakete"
            exit 1
            ;;
    esac
    
    echo ""
    echo "⚠️  Blackmagic DeckLink Support für Linux:"
    echo "   1. Download Desktop Video SDK: https://www.blackmagicdesign.com/support/"
    echo "   2. Installiere Desktop Video Driver"
    echo "   3. Kompiliere gst-plugins-bad mit DeckLink-Support oder"
    echo "   4. Installiere: sudo apt-get install gstreamer1.0-decklink"
    echo ""
fi

# Test der Installation
echo ""
echo "🧪 Teste GStreamer-Installation..."
echo ""

# Test 1: Python GStreamer Bindings
echo "Test 1: Python GStreamer Bindings..."
python3 -c "import gi; gi.require_version('Gst', '1.0'); from gi.repository import Gst; Gst.init(None); print('✅ Python Bindings OK')" || {
    echo "❌ Python Bindings fehlgeschlagen"
    exit 1
}

# Test 2: gst-launch
echo "Test 2: gst-launch-1.0..."
if command -v gst-launch-1.0 &> /dev/null; then
    echo "✅ gst-launch-1.0 gefunden"
else
    echo "❌ gst-launch-1.0 nicht gefunden"
    exit 1
fi

# Test 3: gst-inspect
echo "Test 3: Verfügbare Plugins..."
if command -v gst-inspect-1.0 &> /dev/null; then
    echo "✅ gst-inspect-1.0 gefunden"
    
    # Prüfe wichtige Plugins
    echo ""
    echo "Wichtige Plugins:"
    
    # videoconvert
    if gst-inspect-1.0 videoconvert &> /dev/null; then
        echo "  ✅ videoconvert"
    else
        echo "  ❌ videoconvert (benötigt!)"
    fi
    
    # appsink
    if gst-inspect-1.0 appsink &> /dev/null; then
        echo "  ✅ appsink"
    else
        echo "  ❌ appsink (benötigt!)"
    fi
    
    # v4l2src (Linux)
    if [ "${PLATFORM}" = "Linux" ]; then
        if gst-inspect-1.0 v4l2src &> /dev/null; then
            echo "  ✅ v4l2src (Linux USB-Capture)"
        else
            echo "  ⚠️  v4l2src nicht gefunden"
        fi
    fi
    
    # avfvideosrc (macOS)
    if [ "${PLATFORM}" = "macOS" ]; then
        if gst-inspect-1.0 avfvideosrc &> /dev/null; then
            echo "  ✅ avfvideosrc (macOS Capture)"
        else
            echo "  ⚠️  avfvideosrc nicht gefunden"
        fi
    fi
    
    # decklinkvideosrc (Blackmagic)
    if gst-inspect-1.0 decklinkvideosrc &> /dev/null; then
        echo "  ✅ decklinkvideosrc (Blackmagic DeckLink)"
    else
        echo "  ⚠️  decklinkvideosrc nicht gefunden (DeckLink SDK benötigt)"
    fi
    
else
    echo "❌ gst-inspect-1.0 nicht gefunden"
    exit 1
fi

# Test 4: Verfügbare Video-Devices anzeigen
echo ""
echo "Test 4: Verfügbare Video-Devices..."
if command -v gst-device-monitor-1.0 &> /dev/null; then
    echo "Erkannte Video-Quellen:"
    echo "------------------------"
    gst-device-monitor-1.0 Video | head -n 50 || echo "Keine Devices gefunden"
else
    echo "⚠️  gst-device-monitor-1.0 nicht verfügbar"
fi

echo ""
echo "=================================================="
echo "✅ GStreamer-Installation abgeschlossen!"
echo "=================================================="
echo ""
echo "Nächste Schritte:"
echo "  1. Python-Abhängigkeiten installieren:"
echo "     pip install -r requirements.txt"
echo ""
echo "  2. Konfiguration anpassen:"
echo "     src/config.py → VIDEO_SOURCE = 'gstreamer'"
echo ""
echo "  3. Test der GStreamer-Integration:"
echo "     python3 src/stream/gstreamer_handler.py"
echo ""
echo "  4. PTZ Tracking starten:"
echo "     python3 src/main.py"
echo ""
