"""
PTZ-Controller für Panasonic AW-HE130 Kamera
Steuert Pan/Tilt basierend auf Person-Tracking
"""

import requests
import time
import queue
from typing import Optional, Tuple
from threading import Lock, Thread

from src import config
from src.tracking.person_detector import Detection
from src.utils.logger import get_logger
from src.utils.companion_client import get_companion_client

logger = get_logger(__name__)


class PTZController:
    """
    PTZ-Controller für Panasonic AW-HE130
    
    Features:
    - HTTP-basierte Steuerung über CGI-Befehle
    - Smooth Bewegungen mit konfigurierbarer Geschwindigkeit
    - Dead-Zone zur Vermeidung von Mikrobewegungen
    - Goldener Schnitt für vertikale Positionierung
    - Ein/Aus-Steuerung über Flag
    """
    
    def __init__(
        self,
        camera_ip: str = None,
        camera_port: int = None,
        enabled: bool = None
    ):
        """
        Initialisiert PTZ-Controller
        
        Args:
            camera_ip: IP-Adresse der Kamera (default: config.PTZ_CAMERA_IP)
            camera_port: HTTP-Port (default: config.PTZ_CAMERA_PORT)
            enabled: Initial aktiviert (default: config.PTZ_ENABLED_ON_START)
        """
        self.camera_ip = camera_ip or config.PTZ_CAMERA_IP
        self.camera_port = camera_port or config.PTZ_CAMERA_PORT
        self.enabled = enabled if enabled is not None else config.PTZ_ENABLED_ON_START
        
        # Basis-URL für Kamera-CGI
        self.base_url = f"http://{self.camera_ip}:{self.camera_port}"
        
        # Aktuelle Geschwindigkeiten (smoothed)
        self.current_pan_speed = config.PTZ_SPEED_STOP
        self.current_tilt_speed = config.PTZ_SPEED_STOP
        
        # Thread-Safety
        self.lock = Lock()
        
        # Letzter Update-Timestamp
        self.last_update = 0.0
        
        # Letzter gesendeter Speed (um unnötige Befehle zu vermeiden)
        self.last_sent_pan_speed = None
        self.last_sent_tilt_speed = None
        
        # Companion Client für Custom Variables
        self.companion = get_companion_client()
        
        # Asynchrone Command-Queue (non-blocking PTZ-Befehle)
        self.command_queue = queue.Queue(maxsize=10)  # Max 10 pending commands
        self._shutdown = False
        
        # Worker-Thread für asynchrone HTTP-Requests
        self.worker_thread = Thread(target=self._command_worker, daemon=True, name="PTZ-Worker")
        self.worker_thread.start()
        
        logger.info(f"PTZ-Controller initialisiert (Speed-basiert, Async)")
        logger.info(f"  Kamera: {self.camera_ip}:{self.camera_port}")
        logger.info(f"  Enabled: {self.enabled}")
        logger.info(f"  Target Position: X={config.PTZ_TARGET_X} (center), Headroom={config.PTZ_HEADROOM}")
        logger.info(f"  Speed Range: {config.PTZ_MIN_SPEED}-{config.PTZ_MAX_SPEED}")
        logger.info(f"  Speed Smoothing: {config.PTZ_SPEED_SMOOTHING}")
        logger.info(f"  Speed Ramp: {config.PTZ_SPEED_RAMP}")
        logger.info(f"  Async Queue: Worker-Thread gestartet")
        
        # Initial Companion-Variablen setzen
        self._update_companion_status()
    
    def enable(self):
        """Aktiviert PTZ-Steuerung"""
        with self.lock:
            self.enabled = True
            logger.info("✓ PTZ-Steuerung aktiviert")
            self._update_companion_status()
    
    def disable(self):
        """Deaktiviert PTZ-Steuerung"""
        with self.lock:
            self.enabled = False
            logger.info("✗ PTZ-Steuerung deaktiviert")
            self._update_companion_status()
    
    def is_enabled(self) -> bool:
        """Gibt aktuellen Status zurück"""
        with self.lock:
            return self.enabled
    
    def toggle(self) -> bool:
        """Schaltet PTZ-Steuerung um und gibt neuen Status zurück"""
        with self.lock:
            self.enabled = not self.enabled
            status = "aktiviert" if self.enabled else "deaktiviert"
            logger.info(f"⇄ PTZ-Steuerung {status}")
            self._update_companion_status()
            return self.enabled
    
    def calculate_target_speed(
        self,
        detection: Detection,
        frame_width: int,
        frame_height: int
    ) -> Tuple[int, int]:
        """
        Berechnet Ziel-Speed basierend auf Person-Detection
        
        Speed-basierte Steuerung für broadcast-quality smooth movement:
        - Horizontal: Zentriert auf Augen (nicht Körper-Mitte)
        - Vertikal: Headroom als Abstand BBox-Oberkante zu oberem Bildrand
        - Progressive Annäherung: Je näher am Ziel, desto langsamer
        - Speed 50 = Stop
        - Speed <50 = Bewegung nach links/unten
        - Speed >50 = Bewegung nach rechts/oben
        
        Args:
            detection: Person-Detection mit Bounding-Box und Pose-Keypoints
            frame_width: Frame-Breite in Pixeln
            frame_height: Frame-Höhe in Pixeln
        
        Returns:
            (pan_speed, tilt_speed): Speed-Werte (01-99, 50=Stop)
        """
        # HORIZONTAL: Versuche Augen-Position zu verwenden (broadcast-quality Framing)
        eye_center = detection.get_eye_center(confidence_threshold=config.KEYPOINT_CONFIDENCE_THRESHOLD)
        
        if eye_center is not None:
            # Augen erkannt: Verwende Eye-Center für präzise horizontale Kadrierung
            person_center_x = eye_center[0]
            logger.debug(f"PTZ Framing → Eyes at X={person_center_x:.0f}")
        else:
            # Fallback: BBox-Center verwenden wenn Augen nicht erkannt
            x1, y1, x2, y2 = detection.bbox
            person_center_x = (x1 + x2) / 2.0
            logger.debug(f"PTZ Framing → BBox center X (no eyes detected)")
        
        # VERTIKAL: BBox-Oberkante mit Headroom
        # Headroom = Abstand zwischen y1 (BBox-Oberkante) und oberem Bildrand
        x1, y1, x2, y2 = detection.bbox
        bbox_top = y1  # Obere Kante der Person-BBox
        
        # Normalisierte Positionen (0.0 - 1.0)
        norm_x = person_center_x / frame_width
        norm_bbox_top = bbox_top / frame_height
        
        # Abweichung von Zielposition (-1.0 bis +1.0)
        # X: Augen horizontal zentriert
        # Y: BBox-Top bei Headroom-Abstand vom oberen Rand
        delta_x = norm_x - config.PTZ_TARGET_X
        delta_y = norm_bbox_top - config.PTZ_HEADROOM
        
        logger.debug(f"PTZ Delta → X={delta_x:.3f}, Y={delta_y:.3f} (BBox-Top={norm_bbox_top:.3f}, Target Headroom={config.PTZ_HEADROOM:.3f})")
        
        # Dead-Zone: Keine Bewegung wenn nah genug am Ziel
        if abs(delta_x) < config.PTZ_DEADZONE_X:
            delta_x = 0.0
        if abs(delta_y) < config.PTZ_DEADZONE_Y:
            delta_y = 0.0
        
        # Speed berechnen basierend auf Distanz
        # Progressive Speed: Je größer die Distanz, desto schneller
        # Ramping: Exponentiell verlangsamend je näher am Ziel
        
        def calculate_speed(delta: float, axis: str = 'pan') -> int:
            """
            Berechnet Speed aus Delta mit progressiver Rampe
            
            Args:
                delta: Normalisierte Abweichung (-1.0 bis +1.0)
                axis: 'pan' oder 'tilt'
            
            Returns:
                Speed (01-99, 50=Stop)
            """
            if abs(delta) < 0.001:  # Praktisch am Ziel
                return config.PTZ_SPEED_STOP
            
            # TILT BOOST: Bei Headroom-basierten Tracking ist die Bewegung nach oben
            # typischerweise kleiner als nach unten (Asymmetrie durch Headroom bei 12%).
            # Boost für Aufwärts-Bewegung (positives delta nach Vorzeichenumkehr)
            # delta_y: negativ wenn Person oben → nach Umkehr -delta_y: positiv → Kamera hoch
            if axis == 'tilt' and delta > 0:
                # Verstärke Aufwärts-Bewegung um Faktor 3
                delta = delta * 3.0
            
            # Distanz mit Ramping-Faktor (macht Bewegung progressiver)
            # Ohne Ramping: linear (delta)
            # Mit Ramping: exponentiell (delta^ramp)
            ramped_delta = delta * (abs(delta) ** config.PTZ_SPEED_RAMP)
            
            # Speed berechnen (proportional zu ramped_delta)
            # Speed-Range: MIN_SPEED bis MAX_SPEED
            speed_offset = ramped_delta * config.PTZ_MAX_SPEED
            
            # Minimal-Speed einhalten (außer Stop)
            if abs(speed_offset) > 0:
                if abs(speed_offset) < config.PTZ_MIN_SPEED:
                    speed_offset = config.PTZ_MIN_SPEED if speed_offset > 0 else -config.PTZ_MIN_SPEED
            
            # Zu Speed konvertieren (50 = Stop)
            speed = int(config.PTZ_SPEED_STOP + speed_offset)
            
            # Limits: 01-99
            speed = max(1, min(99, speed))
            
            return speed
        
        pan_speed = calculate_speed(delta_x, 'pan')
        tilt_speed = calculate_speed(-delta_y, 'tilt')  # Vorzeichen umgekehrt: Person zu tief → Kamera runter
        
        return pan_speed, tilt_speed
    
    def update(
        self,
        detection: Optional[Detection],
        frame_width: int,
        frame_height: int
    ) -> bool:
        """
        Update PTZ basierend auf aktuellem Detection
        
        Args:
            detection: Aktuelle Person-Detection (None wenn keine Person)
            frame_width: Frame-Breite
            frame_height: Frame-Höhe
        
        Returns:
            True wenn PTZ bewegt wurde
        """
        # Nicht aktiv -> nichts tun
        if not self.enabled:
            return False
        
        # Rate-Limiting
        now = time.time()
        if now - self.last_update < config.PTZ_UPDATE_INTERVAL:
            return False
        
        self.last_update = now
        
        # Keine Person -> Stop senden
        if detection is None:
            return self._send_stop_command()
        
        # Ziel-Speed berechnen
        target_pan_speed, target_tilt_speed = self.calculate_target_speed(
            detection, frame_width, frame_height
        )
        
        # Speed-Smoothing anwenden (verhindert abrupte Geschwindigkeitswechsel)
        with self.lock:
            # Exponential smoothing für broadcast-quality
            smoothing = config.PTZ_SPEED_SMOOTHING
            self.current_pan_speed = int(
                smoothing * target_pan_speed + (1 - smoothing) * self.current_pan_speed
            )
            self.current_tilt_speed = int(
                smoothing * target_tilt_speed + (1 - smoothing) * self.current_tilt_speed
            )
            
            # PTZ-Speed-Befehl senden (nur wenn sich Speed geändert hat)
            if (self.current_pan_speed != self.last_sent_pan_speed or 
                self.current_tilt_speed != self.last_sent_tilt_speed):
                
                success = self._send_speed_command(self.current_pan_speed, self.current_tilt_speed)
                
                if success:
                    self.last_sent_pan_speed = self.current_pan_speed
                    self.last_sent_tilt_speed = self.current_tilt_speed
                    return True
        
        return False
    
    def _send_speed_command(self, pan_speed: int, tilt_speed: int) -> bool:
        """
        Sendet PTZ-Speed-Befehl asynchron an Kamera (non-blocking)
        
        Args:
            pan_speed: Pan-Geschwindigkeit (01-99, 50=Stop)
            tilt_speed: Tilt-Geschwindigkeit (01-99, 50=Stop)
        
        Returns:
            True wenn Befehl in Queue eingefügt wurde
        """
        try:
            # Befehl in Queue schreiben (non-blocking)
            # Älteste Befehle werden verworfen falls Queue voll (neueste Daten wichtiger)
            try:
                self.command_queue.put_nowait((pan_speed, tilt_speed))
                logger.debug(f"PTZ Command queued → Pan: {pan_speed}, Tilt: {tilt_speed}")
                return True
            except queue.Full:
                # Queue voll → ältesten Befehl verwerfen, neuen einfügen
                try:
                    self.command_queue.get_nowait()  # Ältesten entfernen
                    self.command_queue.put_nowait((pan_speed, tilt_speed))
                    logger.debug(f"PTZ Command queued (dropped oldest) → Pan: {pan_speed}, Tilt: {tilt_speed}")
                    return True
                except:
                    logger.warning("PTZ Command Queue: Fehler beim Verwerfen")
                    return False
        except Exception as e:
            logger.error(f"PTZ Queue Fehler: {e}")
            return False
    
    def _command_worker(self):
        """
        Worker-Thread: Verarbeitet PTZ-Befehle aus Queue asynchron
        
        Läuft in separatem Thread und sendet HTTP-Requests ohne Main-Thread zu blockieren
        """
        logger.info("PTZ Worker-Thread gestartet")
        
        while not self._shutdown:
            try:
                # Warte auf nächsten Befehl (mit Timeout für Shutdown-Check)
                try:
                    pan_speed, tilt_speed = self.command_queue.get(timeout=0.5)
                except queue.Empty:
                    continue  # Kein Befehl → weiter warten
                
                # Befehl ausführen
                self._execute_speed_command(pan_speed, tilt_speed)
                
                # Queue-Task als erledigt markieren
                self.command_queue.task_done()
                
            except Exception as e:
                logger.error(f"PTZ Worker-Thread Fehler: {e}")
        
        logger.info("PTZ Worker-Thread beendet")
    
    def _execute_speed_command(self, pan_speed: int, tilt_speed: int) -> bool:
        """
        Führt PTZ-Speed-Befehl tatsächlich aus (HTTP-Request)
        
        Wird vom Worker-Thread aufgerufen (nicht direkt verwenden!)
        
        Args:
            pan_speed: Pan-Geschwindigkeit (01-99, 50=Stop)
            tilt_speed: Tilt-Geschwindigkeit (01-99, 50=Stop)
        
        Returns:
            True bei Erfolg
        """
        try:
            # Panasonic AW-HE130 CGI-Befehl für Speed-Steuerung:
            # #PTS{pan_speed}{tilt_speed}
            # Speed: 01-99 (2-stellig Dezimal)
            #   01 = maximale Geschwindigkeit links/unten
            #   50 = Stop
            #   99 = maximale Geschwindigkeit rechts/oben
            
            # Speed als 2-stellige Dezimalzahl
            pan_str = f"{pan_speed:02d}"
            tilt_str = f"{tilt_speed:02d}"
            
            # PTS-Befehl konstruieren
            cmd = f"%23PTS{pan_str}{tilt_str}"
            
            # CGI-URL
            # Beispiel: http://192.168.1.100/cgi-bin/aw_ptz?cmd=%23PTS5050&res=1 (Stop)
            url = f"{self.base_url}/cgi-bin/aw_ptz?cmd={cmd}&res=1"
            
            # Log Command URL
            logger.debug(f"PTZ HTTP → {url}")
            
            # HTTP-Request senden (mit Timeout)
            response = requests.get(url, timeout=0.5)
            
            if response.status_code == 200:
                logger.debug(f"PTZ Speed → Pan: {pan_speed}, Tilt: {tilt_speed} [OK]")
                return True
            else:
                logger.warning(f"PTZ-Speed-Befehl fehlgeschlagen: Status {response.status_code} | URL: {url}")
                return False
                
        except requests.exceptions.Timeout:
            logger.warning(f"PTZ-Speed-Befehl Timeout | URL: {url}")
            return False
        except requests.exceptions.ConnectionError:
            logger.error(f"Verbindung zu Kamera fehlgeschlagen: {self.camera_ip} | URL: {url}")
            return False
        except Exception as e:
            logger.error(f"PTZ-Fehler: {e} | URL: {url if 'url' in locals() else 'N/A'}")
            return False
    
    def _send_stop_command(self) -> bool:
        """
        Stoppt PTZ-Bewegung (Speed 50/50)
        
        Returns:
            True bei Erfolg
        """
        with self.lock:
            if (self.last_sent_pan_speed == config.PTZ_SPEED_STOP and 
                self.last_sent_tilt_speed == config.PTZ_SPEED_STOP):
                return False  # Bereits gestoppt
            
            success = self._send_speed_command(config.PTZ_SPEED_STOP, config.PTZ_SPEED_STOP)
            if success:
                self.last_sent_pan_speed = config.PTZ_SPEED_STOP
                self.last_sent_tilt_speed = config.PTZ_SPEED_STOP
                logger.debug("PTZ gestoppt")
            return success
    
    def go_home(self) -> bool:
        """
        Stoppt PTZ-Bewegung (entspricht "Home" in Speed-Modus)
        
        Returns:
            True bei Erfolg
        """
        logger.info("PTZ → Stop (Home)")
        return self._send_stop_command()
    
    def get_status(self) -> dict:
        """
        Gibt aktuellen Status zurück
        
        Returns:
            Dict mit Status-Informationen
        """
        with self.lock:
            return {
                "enabled": self.enabled,
                "camera_ip": self.camera_ip,
                "current_pan_speed": self.current_pan_speed,
                "current_tilt_speed": self.current_tilt_speed,
                "speed_smoothing": config.PTZ_SPEED_SMOOTHING,
                "max_speed": config.PTZ_MAX_SPEED,
                "min_speed": config.PTZ_MIN_SPEED,
                "speed_ramp": config.PTZ_SPEED_RAMP,
                "headroom": config.PTZ_HEADROOM,
                "target_x": config.PTZ_TARGET_X,
            }
    
    def adjust_headroom(self, delta: float) -> float:
        """
        Passt Headroom relativ an (erhöhen/verringern)
        
        Args:
            delta: Änderung des Headrooms (z.B. +0.01 oder -0.01)
        
        Returns:
            Neuer Headroom-Wert
        """
        with self.lock:
            # Neuen Wert berechnen und auf 0.0-0.5 begrenzen
            new_headroom = max(0.0, min(0.5, config.PTZ_HEADROOM + delta))
            config.PTZ_HEADROOM = new_headroom
            logger.info(f"PTZ Headroom angepasst: {new_headroom:.3f} (Δ{delta:+.3f})")
            self._update_companion_headroom()
            return new_headroom
    
    def set_headroom(self, value: float) -> float:
        """
        Setzt Headroom auf absoluten Wert
        
        Args:
            value: Neuer Headroom-Wert (0.0-0.5)
        
        Returns:
            Gesetzter Headroom-Wert
        """
        with self.lock:
            # Auf 0.0-0.5 begrenzen
            new_headroom = max(0.0, min(0.5, value))
            config.PTZ_HEADROOM = new_headroom
            logger.info(f"PTZ Headroom gesetzt: {new_headroom:.3f}")
            self._update_companion_headroom()
            return new_headroom
    
    def _update_companion_status(self):
        """
        Aktualisiert PTZ-Status in Companion Custom Variables
        
        Setzt folgende Variable:
        - ptz_tracking_status: "ON" oder "OFF"
        """
        if not self.companion.is_enabled():
            return
        
        status = "ON" if self.enabled else "OFF"
        self.companion.set_variable("ptz_tracking_status", status)
    
    def _update_companion_headroom(self):
        """
        Aktualisiert Headroom in Companion Custom Variables
        
        Setzt folgende Variable:
        - ptz_headroom: Headroom als Prozent (0-50)
        """
        if not self.companion.is_enabled():
            return
        
        headroom_percent = int(config.PTZ_HEADROOM * 100)
        self.companion.set_variable("ptz_headroom", headroom_percent)
    
    def shutdown(self):
        """
        Beendet PTZ-Controller sauber
        
        Stoppt Worker-Thread und sendet Stop-Command
        """
        logger.info("PTZ-Controller wird heruntergefahren...")
        
        # Stop-Command senden
        self._send_stop_command()
        
        # Worker-Thread beenden
        self._shutdown = True
        
        # Warten auf Thread-Ende (max 2 Sekunden)
        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=2.0)
            if self.worker_thread.is_alive():
                logger.warning("PTZ Worker-Thread konnte nicht sauber beendet werden")
            else:
                logger.info("PTZ Worker-Thread beendet")
        
        logger.info("PTZ-Controller heruntergefahren")
