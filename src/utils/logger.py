"""
Logging-Setup für PTZ Tracking
Zentrales Logging-Modul für die gesamte Anwendung
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Import Konfiguration
try:
    from src import config
except ImportError:
    import config


class ColoredFormatter(logging.Formatter):
    """Formatter für farbige Console-Ausgabe"""
    
    # ANSI Color Codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Grün
        'WARNING': '\033[33m',    # Gelb
        'ERROR': '\033[31m',      # Rot
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',       # Reset
    }
    
    def format(self, record):
        # Farbe basierend auf Log-Level
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Levelname einfärben
        record.levelname = f"{color}{record.levelname}{reset}"
        
        return super().format(record)


def setup_logger(
    name: str = "ptz_tracking",
    level: Optional[str] = None,
    log_to_console: Optional[bool] = None,
    log_to_file: Optional[bool] = None,
    log_file: Optional[Path] = None,
    colored: bool = True
) -> logging.Logger:
    """
    Richtet einen Logger ein
    
    Args:
        name: Name des Loggers
        level: Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_console: Logging in Console aktivieren
        log_to_file: Logging in Datei aktivieren
        log_file: Pfad zur Log-Datei
        colored: Farbige Console-Ausgabe (nur wenn log_to_console=True)
    
    Returns:
        Konfigurierter Logger
    """
    
    # Defaults aus config
    level = level or config.LOG_LEVEL
    log_to_console = log_to_console if log_to_console is not None else config.LOG_TO_CONSOLE
    log_to_file = log_to_file if log_to_file is not None else config.LOG_TO_FILE
    log_file = log_file or config.LOG_FILE
    
    # Logger erstellen
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Vorherige Handler entfernen (falls vorhanden)
    logger.handlers.clear()
    
    # Console-Handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        
        if colored and sys.stdout.isatty():
            # Farbiger Formatter für Terminal
            formatter = ColoredFormatter(
                config.LOG_FORMAT,
                datefmt=config.LOG_DATE_FORMAT
            )
        else:
            # Standard Formatter
            formatter = logging.Formatter(
                config.LOG_FORMAT,
                datefmt=config.LOG_DATE_FORMAT
            )
        
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Datei-Handler
    if log_to_file:
        # Sicherstellen dass Log-Verzeichnis existiert
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper()))
        
        # Formatter ohne Farben für Datei
        formatter = logging.Formatter(
            config.LOG_FORMAT,
            datefmt=config.LOG_DATE_FORMAT
        )
        
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Propagation deaktivieren um doppelte Ausgaben zu vermeiden
    logger.propagate = False
    
    return logger


def get_logger(name: str = "ptz_tracking") -> logging.Logger:
    """
    Holt einen existierenden Logger oder erstellt einen neuen
    
    Args:
        name: Name des Loggers
    
    Returns:
        Logger-Instanz
    """
    logger = logging.getLogger(name)
    
    # Wenn Logger noch keine Handler hat, setup ausführen
    if not logger.handlers:
        logger = setup_logger(name)
    
    return logger


# Globaler Logger für schnellen Zugriff
logger = setup_logger()


# Convenience-Funktionen
def debug(msg: str, *args, **kwargs):
    """Debug-Log"""
    logger.debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs):
    """Info-Log"""
    logger.info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs):
    """Warning-Log"""
    logger.warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs):
    """Error-Log"""
    logger.error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs):
    """Critical-Log"""
    logger.critical(msg, *args, **kwargs)


def exception(msg: str, *args, **kwargs):
    """Exception-Log mit Stack-Trace"""
    logger.exception(msg, *args, **kwargs)


if __name__ == "__main__":
    # Test-Ausgaben
    print("Testing Logger...")
    print("-" * 60)
    
    test_logger = setup_logger("test", level="DEBUG")
    
    test_logger.debug("Dies ist eine Debug-Nachricht")
    test_logger.info("Dies ist eine Info-Nachricht")
    test_logger.warning("Dies ist eine Warning-Nachricht")
    test_logger.error("Dies ist eine Error-Nachricht")
    test_logger.critical("Dies ist eine Critical-Nachricht")
    
    print("-" * 60)
    
    # Test Exception-Logging
    try:
        raise ValueError("Test-Exception")
    except Exception as e:
        test_logger.exception("Exception gefangen:")
    
    print("-" * 60)
    print("Logger-Test abgeschlossen")
