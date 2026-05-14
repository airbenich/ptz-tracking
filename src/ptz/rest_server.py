"""
REST-API Server für PTZ-Steuerung
HTTP-GET Endpoints zum Ein-/Ausschalten der PTZ-Steuerung
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from threading import Thread
import json

from src import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PTZRestHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler für PTZ-REST-API"""
    
    # Referenz zum PTZ-Controller (wird von PTZRestServer gesetzt)
    ptz_controller = None
    
    def log_message(self, format, *args):
        """Überschreibt Standard-Logging (nutzt Python-Logger)"""
        logger.debug(f"REST: {format % args}")
    
    def _send_json_response(self, status_code: int, data: dict):
        """Sendet JSON-Response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')  # CORS
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
    
    def do_GET(self):
        """Behandelt GET-Requests"""
        
        # URL parsen
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        # PTZ-Controller verfügbar?
        if self.ptz_controller is None:
            self._send_json_response(500, {
                "error": "PTZ-Controller nicht verfügbar"
            })
            return
        
        # Endpoints
        
        # GET /ptz/enable - PTZ aktivieren
        if path == '/ptz/enable':
            self.ptz_controller.enable()
            self._send_json_response(200, {
                "success": True,
                "message": "PTZ-Steuerung aktiviert",
                "enabled": True
            })
            return
        
        # GET /ptz/disable - PTZ deaktivieren
        elif path == '/ptz/disable':
            self.ptz_controller.disable()
            self._send_json_response(200, {
                "success": True,
                "message": "PTZ-Steuerung deaktiviert",
                "enabled": False
            })
            return
        
        # GET /ptz/toggle - PTZ umschalten
        elif path == '/ptz/toggle':
            enabled = self.ptz_controller.toggle()
            self._send_json_response(200, {
                "success": True,
                "message": f"PTZ-Steuerung {'aktiviert' if enabled else 'deaktiviert'}",
                "enabled": enabled
            })
            return
        
        # GET /ptz/status - PTZ-Status abfragen
        elif path == '/ptz/status':
            status = self.ptz_controller.get_status()
            self._send_json_response(200, {
                "success": True,
                "status": status
            })
            return
        
        # GET /ptz/home - Zur Home-Position fahren
        elif path == '/ptz/home':
            success = self.ptz_controller.go_home()
            self._send_json_response(200, {
                "success": success,
                "message": "Home-Position angefahren" if success else "Fehler beim Anfahren"
            })
            return
        
        # GET /ptz/headroom/increase - Headroom erhöhen (+1%)
        elif path == '/ptz/headroom/increase':
            delta = 0.01  # 1% erhöhen
            new_headroom = self.ptz_controller.adjust_headroom(delta)
            self._send_json_response(200, {
                "success": True,
                "message": f"Headroom erhöht: {new_headroom:.1%}",
                "headroom": new_headroom,
                "delta": delta
            })
            return
        
        # GET /ptz/headroom/decrease - Headroom verringern (-1%)
        elif path == '/ptz/headroom/decrease':
            delta = -0.01  # 1% verringern
            new_headroom = self.ptz_controller.adjust_headroom(delta)
            self._send_json_response(200, {
                "success": True,
                "message": f"Headroom verringert: {new_headroom:.1%}",
                "headroom": new_headroom,
                "delta": delta
            })
            return
        
        # GET /ptz/headroom/set?value=X - Headroom auf Wert setzen
        elif path == '/ptz/headroom/set':
            # Query-Parameter auslesen
            if 'value' not in query_params:
                self._send_json_response(400, {
                    "error": "Parameter 'value' fehlt",
                    "usage": "/ptz/headroom/set?value=0.12"
                })
                return
            
            try:
                value = float(query_params['value'][0])
                new_headroom = self.ptz_controller.set_headroom(value)
                self._send_json_response(200, {
                    "success": True,
                    "message": f"Headroom gesetzt: {new_headroom:.1%}",
                    "headroom": new_headroom
                })
            except ValueError:
                self._send_json_response(400, {
                    "error": "Ungültiger Wert für 'value'",
                    "usage": "/ptz/headroom/set?value=0.12"
                })
            return
        
        # GET / - Root (API-Info)
        elif path == '/' or path == '':
            self._send_json_response(200, {
                "name": "PTZ Tracking REST API",
                "version": "1.0",
                "endpoints": {
                    "/ptz/enable": "PTZ-Steuerung aktivieren",
                    "/ptz/disable": "PTZ-Steuerung deaktivieren",
                    "/ptz/toggle": "PTZ-Steuerung umschalten",
                    "/ptz/status": "PTZ-Status abfragen",
                    "/ptz/home": "Home-Position anfahren",
                    "/ptz/headroom/increase": "Headroom erhöhen (+1%)",
                    "/ptz/headroom/decrease": "Headroom verringern (-1%)",
                    "/ptz/headroom/set?value=X": "Headroom setzen (0.0-0.5)"
                }
            })
            return
        
        # Unbekannter Endpoint
        else:
            self._send_json_response(404, {
                "error": "Endpoint nicht gefunden",
                "path": path
            })
            return


class PTZRestServer:
    """
    REST-API Server für PTZ-Steuerung
    Läuft in separatem Thread
    """
    
    def __init__(self, ptz_controller, host: str = None, port: int = None):
        """
        Initialisiert REST-Server
        
        Args:
            ptz_controller: PTZController-Instanz
            host: Host-Adresse (default: config.PTZ_REST_HOST)
            port: Port (default: config.PTZ_REST_PORT)
        """
        self.ptz_controller = ptz_controller
        self.host = host or config.PTZ_REST_HOST
        self.port = port or config.PTZ_REST_PORT
        
        # PTZ-Controller an Handler übergeben
        PTZRestHandler.ptz_controller = ptz_controller
        
        # HTTP-Server
        self.httpd = None
        self.server_thread = None
        self.running = False
        
        logger.info(f"PTZ REST-Server initialisiert")
        logger.info(f"  Host: {self.host}:{self.port}")
    
    def start(self):
        """Startet REST-Server in separatem Thread"""
        if self.running:
            logger.warning("REST-Server läuft bereits")
            return
        
        try:
            # HTTP-Server erstellen
            self.httpd = HTTPServer((self.host, self.port), PTZRestHandler)
            
            # Server-Thread starten
            self.server_thread = Thread(
                target=self._run_server,
                daemon=True,
                name="PTZ-REST-Server"
            )
            self.server_thread.start()
            
            self.running = True
            logger.info(f"✓ PTZ REST-Server gestartet auf {self.host}:{self.port}")
            logger.info(f"  Endpoints:")
            logger.info(f"    http://{self.host}:{self.port}/ptz/enable")
            logger.info(f"    http://{self.host}:{self.port}/ptz/disable")
            logger.info(f"    http://{self.host}:{self.port}/ptz/toggle")
            logger.info(f"    http://{self.host}:{self.port}/ptz/status")
            logger.info(f"    http://{self.host}:{self.port}/ptz/headroom/increase")
            logger.info(f"    http://{self.host}:{self.port}/ptz/headroom/decrease")
            logger.info(f"    http://{self.host}:{self.port}/ptz/headroom/set?value=X")
            
        except OSError as e:
            logger.error(f"Fehler beim Starten des REST-Servers: {e}")
            logger.error(f"  Möglicherweise ist Port {self.port} bereits belegt")
            raise
    
    def _run_server(self):
        """Server-Loop (läuft in separatem Thread)"""
        try:
            logger.debug("REST-Server Thread gestartet")
            self.httpd.serve_forever()
        except Exception as e:
            logger.error(f"REST-Server Fehler: {e}")
        finally:
            logger.debug("REST-Server Thread beendet")
    
    def stop(self):
        """Stoppt REST-Server"""
        if not self.running:
            return
        
        logger.info("Stoppe PTZ REST-Server...")
        
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
        
        if self.server_thread:
            self.server_thread.join(timeout=2.0)
        
        self.running = False
        logger.info("✓ PTZ REST-Server gestoppt")
    
    def is_running(self) -> bool:
        """Gibt an ob Server läuft"""
        return self.running
