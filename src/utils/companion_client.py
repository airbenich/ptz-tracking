"""
Bitfocus Companion Client
Push Custom Variables zu Companion via REST API
"""

import requests
from typing import Optional, Any
from src.utils.logger import get_logger
from src import config


logger = get_logger(__name__)


class CompanionClient:
    """
    Client für Bitfocus Companion Custom Variables API
    
    Ermöglicht das Setzen von Custom Variables in Companion für
    Integration mit Buttons, Triggers und anderen Companion-Features.
    """
    
    def __init__(
        self,
        base_url: str = None,
        timeout: float = None,
        enabled: bool = None
    ):
        """
        Args:
            base_url: Companion Server URL (default: config.COMPANION_BASE_URL)
            timeout: Request Timeout (default: config.COMPANION_TIMEOUT)
            enabled: Aktiviert/Deaktiviert Companion-Integration
        """
        self.base_url = base_url or config.COMPANION_BASE_URL
        self.timeout = timeout or config.COMPANION_TIMEOUT
        self.enabled = enabled if enabled is not None else config.COMPANION_ENABLED
        
        if self.enabled:
            logger.info(f"Companion Client initialisiert")
            logger.info(f"  Server: {self.base_url}")
            logger.info(f"  Timeout: {self.timeout}s")
    
    def set_variable(self, name: str, value: Any) -> bool:
        """
        Setzt eine Custom Variable in Companion
        
        API: POST /api/custom-variable/<name>/value?value=<value>
        
        Args:
            name: Variablenname (z.B. "ptz_tracking_status")
            value: Wert der Variable (wird zu String konvertiert)
        
        Returns:
            True wenn erfolgreich, False bei Fehler
        
        Example:
            client.set_variable("ptz_tracking_status", "ON")
            client.set_variable("ptz_headroom", 12)
            client.set_variable("ptz_pan_speed", -5)
        """
        if not self.enabled:
            return False
        
        try:
            # URL erstellen
            url = f"{self.base_url}/api/custom-variable/{name}/value"
            
            # Parameters
            params = {"value": str(value)}
            
            # POST Request
            response = requests.post(
                url,
                params=params,
                timeout=self.timeout
            )
            
            # Erfolg prüfen
            if response.status_code == 200:
                logger.debug(f"Companion Variable gesetzt: {name} = {value}")
                return True
            else:
                logger.warning(
                    f"Companion Variable fehlgeschlagen: {name} = {value} "
                    f"(Status: {response.status_code})"
                )
                return False
        
        except requests.exceptions.Timeout:
            logger.warning(f"Companion Request Timeout: {name}")
            return False
        
        except requests.exceptions.ConnectionError:
            logger.debug(f"Companion nicht erreichbar: {self.base_url}")
            return False
        
        except Exception as e:
            logger.error(f"Companion Fehler bei {name}: {e}")
            return False
    
    def set_variables(self, variables: dict) -> int:
        """
        Setzt mehrere Variables auf einmal
        
        Args:
            variables: Dict mit {name: value} Paaren
        
        Returns:
            Anzahl erfolgreich gesetzter Variables
        
        Example:
            client.set_variables({
                "ptz_status": "ON",
                "ptz_headroom": 12,
                "ptz_pan_speed": 0
            })
        """
        if not self.enabled:
            return 0
        
        success_count = 0
        for name, value in variables.items():
            if self.set_variable(name, value):
                success_count += 1
        
        return success_count
    
    def enable(self):
        """Aktiviert Companion-Integration"""
        self.enabled = True
        logger.info("Companion Client aktiviert")
    
    def disable(self):
        """Deaktiviert Companion-Integration"""
        self.enabled = False
        logger.info("Companion Client deaktiviert")
    
    def is_enabled(self) -> bool:
        """Gibt aktuellen Status zurück"""
        return self.enabled
    
    def test_connection(self) -> bool:
        """
        Testet Verbindung zu Companion
        
        Returns:
            True wenn erreichbar, False sonst
        """
        if not self.enabled:
            return False
        
        try:
            # Versuche eine Test-Variable zu setzen
            result = self.set_variable("ptz_tracking_test", "OK")
            if result:
                logger.info("✓ Companion Verbindung OK")
            return result
        except Exception as e:
            logger.error(f"Companion Verbindungstest fehlgeschlagen: {e}")
            return False


# Singleton-Instanz für einfachen Zugriff
_companion_client = None


def get_companion_client() -> CompanionClient:
    """
    Holt oder erstellt Singleton-Instanz des Companion Clients
    
    Returns:
        CompanionClient Instanz
    """
    global _companion_client
    if _companion_client is None:
        _companion_client = CompanionClient()
    return _companion_client


if __name__ == "__main__":
    # Test Companion Client
    print("Testing Companion Client...")
    print("-" * 60)
    
    client = CompanionClient()
    
    # Verbindung testen
    print("\nTesting connection...")
    client.test_connection()
    
    # Einzelne Variable setzen
    print("\nSetting single variable...")
    client.set_variable("ptz_tracking_status", "ON")
    client.set_variable("ptz_headroom", 12)
    
    # Mehrere Variables setzen
    print("\nSetting multiple variables...")
    count = client.set_variables({
        "ptz_pan_speed": 0,
        "ptz_tilt_speed": 0,
        "ptz_enabled": True,
        "ptz_target_x": 0.5
    })
    print(f"Successfully set {count} variables")
    
    print("-" * 60)
    print("Companion Client Test abgeschlossen")
