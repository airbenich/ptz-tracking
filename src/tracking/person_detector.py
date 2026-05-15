"""
Person Detector
YOLO-basierte Person Detection
"""

from typing import List, Optional, Tuple
import numpy as np

from src.utils.logger import get_logger
from src import config


logger = get_logger(__name__)


class Detection:
    """
    Einzelne Person Detection
    """
    
    def __init__(
        self,
        bbox: Tuple[int, int, int, int],
        confidence: float,
        class_id: int = 0,
        keypoints: Optional[np.ndarray] = None
    ):
        """
        Args:
            bbox: (x1, y1, x2, y2) Bounding Box
            confidence: Konfidenz-Score (0.0 - 1.0)
            class_id: Klassen-ID (0 = Person)
            keypoints: Pose-Keypoints als numpy array (n, 3) mit (x, y, confidence)
        """
        self.bbox = bbox
        self.confidence = confidence
        self.class_id = class_id
        self.keypoints = keypoints
    
    @property
    def x1(self) -> int:
        return self.bbox[0]
    
    @property
    def y1(self) -> int:
        return self.bbox[1]
    
    @property
    def x2(self) -> int:
        return self.bbox[2]
    
    @property
    def y2(self) -> int:
        return self.bbox[3]
    
    @property
    def width(self) -> int:
        return self.x2 - self.x1
    
    @property
    def height(self) -> int:
        return self.y2 - self.y1
    
    @property
    def area(self) -> int:
        return self.width * self.height
    
    @property
    def center(self) -> Tuple[int, int]:
        """Returns: (center_x, center_y)"""
        return (
            self.x1 + self.width // 2,
            self.y1 + self.height // 2
        )
    
    def get_visible_keypoints(self, confidence_threshold: float = 0.3) -> np.ndarray:
        """
        Gibt nur Keypoints mit ausreichender Konfidenz zurück
        
        Args:
            confidence_threshold: Minimale Konfidenz für Keypoint
            
        Returns:
            Gefilterte Keypoints (n, 3) mit (x, y, confidence)
        """
        if self.keypoints is None or len(self.keypoints) == 0:
            return np.array([])
        
        # Filtere Keypoints nach Konfidenz
        mask = self.keypoints[:, 2] >= confidence_threshold
        return self.keypoints[mask]
    
    def has_pose(self) -> bool:
        """Prüft ob Pose-Daten vorhanden sind"""
        return self.keypoints is not None and len(self.keypoints) > 0
    
    def get_eye_center(self, confidence_threshold: float = 0.3) -> Optional[Tuple[float, float]]:
        """
        Berechnet die Position zwischen beiden Augen (für broadcast-quality Framing)
        
        YOLO Pose Keypoint-Indizes:
        - 0: Nose
        - 1: Left Eye
        - 2: Right Eye
        - 3: Left Ear
        - 4: Right Ear
        
        Args:
            confidence_threshold: Minimale Konfidenz für Keypoints
            
        Returns:
            (eye_center_x, eye_center_y) oder None wenn Augen nicht erkannt
        """
        if not self.has_pose() or len(self.keypoints) < 3:
            return None
        
        # Left Eye (Index 1) und Right Eye (Index 2)
        left_eye = self.keypoints[1]  # [x, y, confidence]
        right_eye = self.keypoints[2]  # [x, y, confidence]
        
        # Prüfe ob beide Augen sichtbar sind
        left_eye_visible = left_eye[2] >= confidence_threshold
        right_eye_visible = right_eye[2] >= confidence_threshold
        
        if left_eye_visible and right_eye_visible:
            # Beide Augen: Mittelpunkt verwenden
            eye_center_x = (left_eye[0] + right_eye[0]) / 2.0
            eye_center_y = (left_eye[1] + right_eye[1]) / 2.0
            return (eye_center_x, eye_center_y)
        
        elif left_eye_visible:
            # Nur linkes Auge sichtbar
            return (float(left_eye[0]), float(left_eye[1]))
        
        elif right_eye_visible:
            # Nur rechtes Auge sichtbar
            return (float(right_eye[0]), float(right_eye[1]))
        
        # Fallback: Nase verwenden wenn Augen nicht sichtbar
        nose = self.keypoints[0]
        if nose[2] >= confidence_threshold:
            return (float(nose[0]), float(nose[1]))
        
        return None
    
    def get_head_bbox(self, confidence_threshold: float = 0.3) -> Optional[Tuple[int, int, int, int]]:
        """
        Berechnet Bounding Box für den Kopf basierend auf Gesichts-Features
        
        - Oberkante: BBox-Oberkante (y1) der Person
        - Seitlich: Berechnet aus Gesichts-Features (Augen, Ohren)
        - Unterkante: Gleiche Höhe wie zur Oberkante
        
        Args:
            confidence_threshold: Minimale Konfidenz für Keypoints
        
        Returns:
            (x1, y1, x2, y2) Kopf-BBox oder None wenn keine Features
        """
        if not self.has_pose() or len(self.keypoints) < 5:
            return None
        
        # Gesichts-Keypoints: 0=Nose, 1=Left Eye, 2=Right Eye, 3=Left Ear, 4=Right Ear
        face_keypoints = self.keypoints[0:5]
        
        # Filtere sichtbare Keypoints
        visible = []
        for i, kpt in enumerate(face_keypoints):
            if kpt[2] >= confidence_threshold:
                visible.append((i, kpt[0], kpt[1]))  # (index, x, y)
        
        if len(visible) < 2:
            return None
        
        # Berechne horizontale Ausdehnung aus sichtbaren Features
        xs = [kpt[1] for kpt in visible]
        min_x = min(xs)
        max_x = max(xs)
        
        # Breite mit Padding (20% auf jeder Seite)
        width = max_x - min_x
        padding = width * 0.2
        
        head_x1 = int(min_x - padding)
        head_x2 = int(max_x + padding)
        head_width = head_x2 - head_x1
        
        # Oberkante: BBox-Oberkante der Person
        head_y1 = self.y1
        
        # Höhe: Gleiche Höhe wie die Breite (quadratisch)
        # Alternativ: Proportional zur Breite für realistischere Kopf-Proportionen
        head_height = int(head_width * 1.2)  # Kopf ist typischerweise etwas höher als breit
        
        head_y2 = head_y1 + head_height
        
        return (head_x1, head_y1, head_x2, head_y2)
    
    def __repr__(self) -> str:
        pose_info = f", pose={len(self.keypoints) if self.has_pose() else 0} kpts" if self.has_pose() else ""
        return f"Detection(bbox={self.bbox}, conf={self.confidence:.2f}{pose_info})"


class PersonDetector:
    """
    YOLO-basierte Person Detection
    """
    
    def __init__(
        self,
        model_path: str = None,
        confidence_threshold: float = None,
        device: str = None,
        enable_pose: bool = None
    ):
        """
        Args:
            model_path: Pfad zum YOLO-Modell
            confidence_threshold: Minimale Konfidenz
            device: Device für Inference (cuda, mps, cpu)
            enable_pose: Pose-Estimation aktivieren
        """
        # Pose-Estimation aktivieren?
        self.enable_pose = enable_pose if enable_pose is not None else config.ENABLE_POSE_ESTIMATION
        
        # Modell-Pfad anpassen wenn Pose aktiviert ist
        if self.enable_pose and model_path is None:
            self.model_path = str(config.MODELS_DIR / config.POSE_MODEL)
        else:
            self.model_path = model_path or str(config.MODELS_DIR / config.MODEL)
        
        self.confidence_threshold = confidence_threshold or config.CONFIDENCE_THRESHOLD
        self.device = device or config.DEVICE
        
        self.model = None
        
        logger.info(f"Person Detector initialisiert")
        logger.info(f"Modell: {self.model_path}")
        logger.info(f"Device: {self.device}")
        logger.info(f"Confidence: {self.confidence_threshold}")
        logger.info(f"Pose-Estimation: {self.enable_pose}")
    
    def load_model(self):
        """
        Lädt das YOLO-Modell
        """
        try:
            logger.info("Lade YOLO-Modell...")
            
            from ultralytics import YOLO
            
            # Modell laden
            self.model = YOLO(self.model_path)
            
            # Auf Device verschieben (YOLO macht das automatisch)
            # Beim ersten Aufruf wird das Modell aufs Device geladen
            
            logger.info(f"✓ YOLO-Modell geladen: {self.model_path}")
            logger.info(f"  Device: {self.device}")
            
        except ImportError:
            logger.error("ultralytics nicht installiert. Bitte installieren: pip install ultralytics")
            raise
        except FileNotFoundError:
            logger.error(f"Modell nicht gefunden: {self.model_path}")
            logger.info("YOLO lädt das Modell beim ersten Mal automatisch herunter.")
            raise
        except Exception as e:
            logger.error(f"Fehler beim Laden des Modells: {e}")
            raise
    
    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Erkennt Personen im Frame
        
        Args:
            frame: Input-Frame (BGR, NumPy-Array)
        
        Returns:
            Liste von Detection-Objekten
        """
        if self.model is None:
            logger.warning("Modell nicht geladen. Rufe load_model() zuerst auf.")
            return []
        
        try:
            # Inference durchführen
            # verbose=False unterdrückt YOLO-Output
            # conf=threshold setzt minimale Confidence
            # device wird automatisch verwendet
            results = self.model(
                frame,
                conf=self.confidence_threshold,
                verbose=False,
                device=self.device
            )
            
            # Results parsen (nur erste Result, da wir nur ein Bild übergeben)
            detections = self._parse_results(results[0])
            
            return detections
            
        except Exception as e:
            logger.error(f"Fehler bei Detection: {e}")
            return []
    
    def _parse_results(self, results) -> List[Detection]:
        """
        Parst YOLO-Results zu Detection-Objekten
        
        Args:
            results: YOLO Results (einzelnes Result-Objekt)
        
        Returns:
            Liste von Detections (nur Personen)
        """
        detections = []
        
        # Prüfe ob Detections vorhanden sind
        if results.boxes is None or len(results.boxes) == 0:
            return detections
        
        # Iteriere über alle Detections
        for i, box in enumerate(results.boxes):
            # Klassen-ID extrahieren (als int)
            class_id = int(box.cls[0])
            
            # Nur Personen (class_id=0 in COCO-Dataset)
            if class_id != 0:
                continue
            
            # Bounding Box extrahieren (xyxy Format)
            # box.xyxy ist ein Tensor, zu numpy konvertieren
            xyxy = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = map(int, xyxy)
            
            # Confidence extrahieren
            confidence = float(box.conf[0])
            
            # Keypoints extrahieren (wenn Pose-Modell verwendet wird)
            keypoints = None
            if self.enable_pose and hasattr(results, 'keypoints') and results.keypoints is not None:
                try:
                    # Keypoints für diese Detection
                    # Format: (17, 3) für COCO-Pose mit 17 Keypoints (x, y, confidence)
                    kpts = results.keypoints.data[i].cpu().numpy()
                    
                    # Prüfe ob Keypoints vorhanden sind
                    if kpts.shape[0] > 0:
                        keypoints = kpts
                except Exception as e:
                    logger.debug(f"Fehler beim Extrahieren der Keypoints: {e}")
            
            # Detection-Objekt erstellen
            detection = Detection(
                bbox=(x1, y1, x2, y2),
                confidence=confidence,
                class_id=class_id,
                keypoints=keypoints
            )
            
            detections.append(detection)
        
        return detections


if __name__ == "__main__":
    # Test
    import cv2
    
    logger.info("=" * 60)
    logger.info("Testing Person Detector...")
    logger.info("=" * 60)
    
    # Detector erstellen
    detector = PersonDetector()
    
    # Modell laden
    logger.info("\n1. Lade Modell...")
    detector.load_model()
    
    # Test mit schwarzem Frame (sollte nichts erkennen)
    logger.info("\n2. Test mit leerem Frame...")
    dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    detections = detector.detect(dummy_frame)
    logger.info(f"   Detections: {len(detections)} (erwartet: 0)")
    
    # Test mit weißem Frame (sollte auch nichts erkennen)
    logger.info("\n3. Test mit weißem Frame...")
    white_frame = np.ones((720, 1280, 3), dtype=np.uint8) * 255
    detections = detector.detect(white_frame)
    logger.info(f"   Detections: {len(detections)} (erwartet: 0)")
    
    # Test mit zufälligem Noise
    logger.info("\n4. Test mit Random-Noise...")
    noise_frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
    detections = detector.detect(noise_frame)
    logger.info(f"   Detections: {len(detections)} (sollte 0 oder sehr wenig sein)")
    
    if detections:
        for i, det in enumerate(detections):
            logger.info(f"   Detection {i+1}: {det}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ Person Detector Tests abgeschlossen")
    logger.info("=" * 60)
    logger.info("\nHinweis: Für realistische Tests verwende:")
    logger.info("  - Webcam: python examples/detection_example.py")
    logger.info("  - Video-Datei mit Personen")
    logger.info("  - Oder erstelle ein Testbild mit einer Person")
