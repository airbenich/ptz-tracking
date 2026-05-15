"""
Multi-Person Tracker
Trackt alle erkannten Personen mit persistenten IDs und erlaubt manuelle Auswahl
"""

from typing import List, Optional, Dict
import numpy as np
from collections import deque

from src.utils.logger import get_logger
from src.tracking.person_detector import Detection
from src import config


logger = get_logger(__name__)


class TrackedPerson:
    """
    Eine getrackte Person mit persistenter ID und Historie
    """
    
    def __init__(self, track_id: int, detection: Detection):
        """
        Args:
            track_id: Eindeutige Track-ID
            detection: Initiale Detection
        """
        self.track_id = track_id
        self.detection = detection
        self.frames_since_last_seen = 0
        self.total_frames_tracked = 1
        self.center_history = deque(maxlen=30)  # Letzte 30 Zentren
        self.center_history.append(detection.center)
        
    def update(self, detection: Detection):
        """
        Aktualisiert Track mit neuer Detection
        
        Args:
            detection: Neue Detection dieser Person
        """
        self.detection = detection
        self.frames_since_last_seen = 0
        self.total_frames_tracked += 1
        self.center_history.append(detection.center)
        
    def mark_missing(self):
        """Markiert Person als nicht in diesem Frame gesehen"""
        self.frames_since_last_seen += 1
    
    @property
    def is_active(self) -> bool:
        """Gibt zurück ob Track noch aktiv ist"""
        return self.frames_since_last_seen < config.MAX_FRAMES_WITHOUT_DETECTION
    
    @property
    def velocity(self) -> float:
        """
        Berechnet durchschnittliche Bewegungsgeschwindigkeit
        
        Returns:
            Geschwindigkeit in Pixeln pro Frame
        """
        if len(self.center_history) < 2:
            return 0.0
        
        distances = []
        centers = list(self.center_history)
        for i in range(1, len(centers)):
            dx = centers[i][0] - centers[i-1][0]
            dy = centers[i][1] - centers[i-1][1]
            distances.append((dx**2 + dy**2) ** 0.5)
        
        return sum(distances) / len(distances) if distances else 0.0
    
    def to_dict(self) -> dict:
        """
        Konvertiert Track zu Dictionary für API-Responses
        
        Returns:
            Track-Informationen als Dictionary
        """
        return {
            "track_id": self.track_id,
            "bbox": self.detection.bbox,
            "center": self.detection.center,
            "confidence": self.detection.confidence,
            "area": self.detection.area,
            "frames_tracked": self.total_frames_tracked,
            "velocity": round(self.velocity, 2),
            "is_active": self.is_active
        }


class MultiPersonTracker:
    """
    Trackt mehrere Personen gleichzeitig mit persistenten IDs
    Erlaubt manuelle Auswahl der zu verfolgenden Person
    """
    
    def __init__(
        self,
        max_distance_threshold: float = None,
        smoothing_enabled: bool = None,
        smoothing_factor: float = None
    ):
        """
        Args:
            max_distance_threshold: Max. Distanz für Track-Zuordnung (Pixel)
            smoothing_enabled: Smoothing aktivieren
            smoothing_factor: Smoothing-Faktor (0.0 - 1.0)
        """
        self.max_distance_threshold = max_distance_threshold or config.MULTI_PERSON_MAX_DISTANCE
        self.smoothing_enabled = smoothing_enabled if smoothing_enabled is not None else config.SMOOTHING_ENABLED
        self.smoothing_factor = smoothing_factor or config.SMOOTHING_FACTOR
        
        self.tracks: Dict[int, TrackedPerson] = {}  # track_id -> TrackedPerson
        self.next_track_id = 1
        self.active_track_id: Optional[int] = None  # Manuell ausgewählte Person
        
        self.smoothed_bbox: Optional[tuple] = None
        self.smoothed_keypoints: Optional[np.ndarray] = None
        
        logger.info(f"Multi-Person Tracker initialisiert")
        logger.info(f"Max Distance: {self.max_distance_threshold}px")
        logger.info(f"Smoothing: {self.smoothing_enabled} (Factor: {self.smoothing_factor})")
    
    def update(self, detections: List[Detection], frame_shape: tuple) -> Optional[Detection]:
        """
        Aktualisiert alle Tracks mit neuen Detections
        
        Args:
            detections: Liste von Person Detections
            frame_shape: (height, width, channels)
        
        Returns:
            Detection der aktiv verfolgten Person oder None
        """
        # 1. Bestehende Tracks mit neuen Detections matchen
        matched_tracks, matched_detections = self._match_detections_to_tracks(detections)
        
        # 2. Matched Tracks aktualisieren
        for track_id, detection in zip(matched_tracks, matched_detections):
            self.tracks[track_id].update(detection)
        
        # 3. Unmatched Detections als neue Tracks hinzufügen
        unmatched_detections = [
            det for i, det in enumerate(detections) 
            if i not in [detections.index(d) for d in matched_detections]
        ]
        
        for detection in unmatched_detections:
            self._create_new_track(detection)
        
        # 4. Alle nicht gematchten Tracks als "missing" markieren
        for track_id, track in self.tracks.items():
            if track_id not in matched_tracks:
                track.mark_missing()
        
        # 5. Inaktive Tracks entfernen
        self._remove_inactive_tracks()
        
        # 6. Wenn keine aktive Person gewählt: Wähle größte/prominenteste
        if self.active_track_id is None or self.active_track_id not in self.tracks:
            self._auto_select_active_track()
        
        # 7. Detection der aktiven Person zurückgeben
        return self.get_active_detection()
    
    def _match_detections_to_tracks(
        self,
        detections: List[Detection]
    ) -> tuple[List[int], List[Detection]]:
        """
        Matched Detections zu bestehenden Tracks (einfaches Center-Distance Matching)
        
        Args:
            detections: Neue Detections
        
        Returns:
            (matched_track_ids, matched_detections)
        """
        if not self.tracks or not detections:
            return [], []
        
        matched_tracks = []
        matched_detections = []
        used_detection_indices = set()
        
        # Für jeden Track: Finde nächste Detection
        for track_id, track in self.tracks.items():
            if not track.is_active:
                continue
            
            best_distance = float('inf')
            best_detection_idx = None
            
            for i, detection in enumerate(detections):
                if i in used_detection_indices:
                    continue
                
                # Berechne Distanz zwischen Track-Center und Detection-Center
                distance = self._calculate_distance(track.detection.center, detection.center)
                
                if distance < best_distance and distance < self.max_distance_threshold:
                    best_distance = distance
                    best_detection_idx = i
            
            # Wenn Match gefunden
            if best_detection_idx is not None:
                matched_tracks.append(track_id)
                matched_detections.append(detections[best_detection_idx])
                used_detection_indices.add(best_detection_idx)
        
        return matched_tracks, matched_detections
    
    def _calculate_distance(self, point1: tuple, point2: tuple) -> float:
        """
        Berechnet euklidische Distanz zwischen zwei Punkten
        
        Args:
            point1: (x, y)
            point2: (x, y)
        
        Returns:
            Distanz in Pixeln
        """
        dx = point1[0] - point2[0]
        dy = point1[1] - point2[1]
        return (dx**2 + dy**2) ** 0.5
    
    def _create_new_track(self, detection: Detection) -> int:
        """
        Erstellt neuen Track für eine Detection
        
        Args:
            detection: Neue Detection
        
        Returns:
            Track-ID
        """
        track_id = self.next_track_id
        self.tracks[track_id] = TrackedPerson(track_id, detection)
        self.next_track_id += 1
        
        logger.debug(f"Neuer Track erstellt: ID={track_id} @ {detection.center}")
        return track_id
    
    def _remove_inactive_tracks(self):
        """Entfernt Tracks die zu lange nicht mehr gesehen wurden"""
        inactive_ids = [
            track_id for track_id, track in self.tracks.items()
            if not track.is_active
        ]
        
        for track_id in inactive_ids:
            logger.debug(f"Track entfernt: ID={track_id} (inaktiv)")
            del self.tracks[track_id]
    
    def _auto_select_active_track(self):
        """
        Wählt automatisch einen Track als aktiven Track
        (größte Person / höchste Konfidenz)
        """
        if not self.tracks:
            self.active_track_id = None
            return
        
        # Wähle Track mit größter Bounding Box Area
        best_track = max(
            self.tracks.values(),
            key=lambda t: t.detection.area,
            default=None
        )
        
        if best_track:
            self.active_track_id = best_track.track_id
            logger.debug(f"Auto-Select: Track ID={self.active_track_id}")
    
    def get_active_detection(self) -> Optional[Detection]:
        """
        Gibt Detection der aktiv verfolgten Person zurück
        
        Returns:
            Detection oder None
        """
        if self.active_track_id is None or self.active_track_id not in self.tracks:
            return None
        
        detection = self.tracks[self.active_track_id].detection
        
        # Smoothing anwenden wenn aktiviert
        if self.smoothing_enabled:
            detection = self._apply_smoothing(detection)
        
        return detection
    
    def _apply_smoothing(self, detection: Detection) -> Detection:
        """
        Wendet Smoothing auf Bounding Box und Keypoints an
        
        Args:
            detection: Neue Detection
        
        Returns:
            Detection mit geglätteter Bounding Box und Keypoints
        """
        # BBox Smoothing
        if not self.smoothed_bbox:
            self.smoothed_bbox = detection.bbox
            self.smoothed_keypoints = detection.keypoints.copy() if detection.has_pose() else None
            logger.debug(f"Smoothing initialisiert (Factor: {self.smoothing_factor})")
            return detection
        
        # Exponential Smoothing für BBox
        alpha = 1 - self.smoothing_factor
        
        smoothed_bbox = tuple(
            int(alpha * new + (1 - alpha) * old)
            for new, old in zip(detection.bbox, self.smoothed_bbox)
        )
        
        # Debug: BBox-Änderung loggen
        bbox_change = sum(abs(n - o) for n, o in zip(detection.bbox, self.smoothed_bbox)) / 4
        logger.debug(f"BBox Smoothing: alpha={alpha:.2f}, avg_change={bbox_change:.1f}px")
        
        self.smoothed_bbox = smoothed_bbox
        
        # Keypoint Smoothing
        smoothed_keypoints = None
        if detection.has_pose() and detection.keypoints is not None:
            if self.smoothed_keypoints is not None and len(self.smoothed_keypoints) == len(detection.keypoints):
                # Glätte jedes Keypoint (x, y, confidence)
                smoothed_keypoints = np.zeros_like(detection.keypoints)
                total_kpt_change = 0
                visible_count = 0
                
                for i, (new_kpt, old_kpt) in enumerate(zip(detection.keypoints, self.smoothed_keypoints)):
                    # Nur x und y glätten, confidence direkt übernehmen
                    smoothed_keypoints[i][0] = alpha * new_kpt[0] + (1 - alpha) * old_kpt[0]
                    smoothed_keypoints[i][1] = alpha * new_kpt[1] + (1 - alpha) * old_kpt[1]
                    smoothed_keypoints[i][2] = new_kpt[2]  # Confidence nicht glätten
                    
                    # Debug: Änderung berechnen
                    if new_kpt[2] >= 0.3:  # Nur sichtbare Keypoints
                        change = np.sqrt((new_kpt[0] - old_kpt[0])**2 + (new_kpt[1] - old_kpt[1])**2)
                        total_kpt_change += change
                        visible_count += 1
                
                self.smoothed_keypoints = smoothed_keypoints
                
                # Debug: Durchschnittliche Keypoint-Änderung
                if visible_count > 0:
                    avg_kpt_change = total_kpt_change / visible_count
                    logger.debug(f"Keypoint Smoothing: {visible_count} visible, avg_change={avg_kpt_change:.1f}px")
            else:
                # Erste Detection mit Keypoints oder Anzahl hat sich geändert
                smoothed_keypoints = detection.keypoints.copy()
                self.smoothed_keypoints = smoothed_keypoints
                logger.debug("Keypoint Smoothing: Initialisiert (erste Detection)")
        else:
            smoothed_keypoints = detection.keypoints
        
        return Detection(
            bbox=smoothed_bbox,
            confidence=detection.confidence,
            class_id=detection.class_id,
            keypoints=smoothed_keypoints
        )
    
    def select_next_person(self) -> Optional[int]:
        """
        Wechselt zur nächsten getracken Person (loop)
        
        Returns:
            Neue aktive Track-ID oder None
        """
        if not self.tracks:
            self.active_track_id = None
            return None
        
        # Alle Track-IDs sortiert
        track_ids = sorted(self.tracks.keys())
        
        if self.active_track_id is None:
            # Wähle erste Person
            self.active_track_id = track_ids[0]
        else:
            # Finde aktuellen Index
            try:
                current_index = track_ids.index(self.active_track_id)
                # Nächster Index (mit wrap-around)
                next_index = (current_index + 1) % len(track_ids)
                self.active_track_id = track_ids[next_index]
            except ValueError:
                # Aktuelle ID existiert nicht mehr, wähle erste
                self.active_track_id = track_ids[0]
        
        # Reset Smoothing bei Person-Wechsel
        self.smoothed_bbox = None
        self.smoothed_keypoints = None
        
        logger.info(f"Person gewechselt zu Track ID={self.active_track_id}")
        return self.active_track_id
    
    def select_person_by_id(self, track_id: int) -> bool:
        """
        Wählt spezifische Person per Track-ID
        
        Args:
            track_id: Track-ID der zu verfolgenden Person
        
        Returns:
            True wenn erfolgreich, False wenn ID nicht existiert
        """
        if track_id in self.tracks:
            self.active_track_id = track_id
            self.smoothed_bbox = None  # Reset Smoothing
            self.smoothed_keypoints = None
            logger.info(f"Person manuell gewählt: Track ID={track_id}")
            return True
        else:
            logger.warning(f"Track ID={track_id} existiert nicht")
            return False
    
    def get_all_tracks(self) -> List[TrackedPerson]:
        """
        Gibt alle aktiven Tracks zurück
        
        Returns:
            Liste aller TrackedPerson Objekte
        """
        return list(self.tracks.values())
    
    def get_status(self) -> dict:
        """
        Gibt Status des Trackers zurück (für REST-API)
        
        Returns:
            Status-Dictionary
        """
        return {
            "total_tracks": len(self.tracks),
            "active_track_id": self.active_track_id,
            "tracks": [track.to_dict() for track in self.tracks.values()]
        }
    
    def reset(self):
        """Setzt Tracker komplett zurück"""
        self.tracks.clear()
        self.next_track_id = 1
        self.active_track_id = None
        self.smoothed_bbox = None
        logger.info("Multi-Person Tracker zurückgesetzt")
