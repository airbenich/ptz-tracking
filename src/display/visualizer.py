"""
Visualizer
OpenCV-basierte Visualisierung für Tracking-Daten
"""

import cv2
import numpy as np
from typing import Optional

from src.utils.logger import get_logger
from src.tracking.person_detector import Detection
from src.utils.performance import FPSCounter, SystemStats
from src import config


logger = get_logger(__name__)


# COCO Pose Skeleton Verbindungen
# Format: (start_keypoint_index, end_keypoint_index)
# COCO Pose hat 17 Keypoints:
# 0: nose, 1: left_eye, 2: right_eye, 3: left_ear, 4: right_ear,
# 5: left_shoulder, 6: right_shoulder, 7: left_elbow, 8: right_elbow,
# 9: left_wrist, 10: right_wrist, 11: left_hip, 12: right_hip,
# 13: left_knee, 14: right_knee, 15: left_ankle, 16: right_ankle
SKELETON_CONNECTIONS = [
    (0, 1), (0, 2),  # Kopf
    (1, 3), (2, 4),  # Ohren
    (5, 6),  # Schultern
    (5, 7), (7, 9),  # Linker Arm
    (6, 8), (8, 10),  # Rechter Arm
    (5, 11), (6, 12),  # Torso
    (11, 12),  # Hüften
    (11, 13), (13, 15),  # Linkes Bein
    (12, 14), (14, 16),  # Rechtes Bein
]


class Visualizer:
    """
    Visualisiert Tracking-Daten mit OpenCV
    """
    
    @staticmethod
    def draw_bbox_corners(
        frame: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        color: tuple,
        thickness: int = 2,
        corner_length: int = 20
    ) -> None:
        """
        Zeichnet nur die 4 Ecken einer BBox als rechte Winkel
        
        Args:
            frame: Frame zum Zeichnen
            x1, y1: Obere linke Ecke
            x2, y2: Untere rechte Ecke
            color: Farbe der Ecken
            thickness: Linienstärke
            corner_length: Länge der Ecken-Linien in Pixel
        """
        # Oben links
        cv2.line(frame, (x1, y1), (x1 + corner_length, y1), color, thickness)
        cv2.line(frame, (x1, y1), (x1, y1 + corner_length), color, thickness)
        
        # Oben rechts
        cv2.line(frame, (x2, y1), (x2 - corner_length, y1), color, thickness)
        cv2.line(frame, (x2, y1), (x2, y1 + corner_length), color, thickness)
        
        # Unten links
        cv2.line(frame, (x1, y2), (x1 + corner_length, y2), color, thickness)
        cv2.line(frame, (x1, y2), (x1, y2 - corner_length), color, thickness)
        
        # Unten rechts
        cv2.line(frame, (x2, y2), (x2 - corner_length, y2), color, thickness)
        cv2.line(frame, (x2, y2), (x2, y2 - corner_length), color, thickness)
    
    def __init__(
        self,
        window_name: str = None,
        display_size: tuple = None,
        fullscreen: bool = None,
        show_fps: bool = None,
        show_info: bool = None
    ):
        """
        Args:
            window_name: Name des OpenCV-Windows
            display_size: (width, height) für Display
            fullscreen: Vollbild-Modus
            show_fps: FPS-Counter anzeigen
            show_info: Tracking-Infos anzeigen
        """
        self.window_name = window_name or config.WINDOW_NAME
        self.display_size = display_size or (config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT)
        self.fullscreen = fullscreen if fullscreen is not None else config.FULLSCREEN
        self.show_fps = show_fps if show_fps is not None else config.SHOW_FPS
        self.show_info = show_info if show_info is not None else config.SHOW_INFO
        
        self.fps_counter = FPSCounter()
        self.system_stats = SystemStats()
        self.window_created = False
        
        logger.info(f"Visualizer initialisiert")
        logger.info(f"Display: {self.display_size[0]}x{self.display_size[1]}")
    
    def create_window(self):
        """
        Erstellt OpenCV-Window
        """
        if self.window_created:
            return
        
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, self.display_size[0], self.display_size[1])
        
        if self.fullscreen:
            cv2.setWindowProperty(
                self.window_name,
                cv2.WND_PROP_FULLSCREEN,
                cv2.WINDOW_FULLSCREEN
            )
        
        self.window_created = True
        logger.info(f"Window erstellt: {self.window_name}")
    
    def draw_detection(
        self,
        frame: np.ndarray,
        detection: Optional[Detection]
    ) -> np.ndarray:
        """
        Zeichnet Detection auf Frame
        
        Args:
            frame: Input-Frame
            detection: Detection-Objekt oder None
        
        Returns:
            Frame mit gezeichneter Detection
        """
        if detection is None:
            return frame
        
        # Bounding Box zeichnen (falls aktiviert)
        if config.SHOW_BBOX:
            cv2.rectangle(
                frame,
                (detection.x1, detection.y1),
                (detection.x2, detection.y2),
                config.BBOX_COLOR,
                config.BBOX_THICKNESS
            )
        
        # Label (falls BBox aktiviert)
        if config.SHOW_BBOX:
            label = f"Person {detection.confidence:.2f}"
            label_size, _ = cv2.getTextSize(
                label,
                cv2.FONT_HERSHEY_SIMPLEX,
                config.TEXT_SCALE,
                config.TEXT_THICKNESS
            )
            
            # Label-Hintergrund
            cv2.rectangle(
                frame,
                (detection.x1, detection.y1 - label_size[1] - 10),
                (detection.x1 + label_size[0], detection.y1),
                config.BBOX_COLOR,
                -1
            )
            
            # Label-Text
            cv2.putText(
                frame,
                label,
                (detection.x1, detection.y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                config.TEXT_SCALE,
                (0, 0, 0),
                config.TEXT_THICKNESS
            )
        
        return frame
    
    def draw_multi_person_tracking(
        self,
        frame: np.ndarray,
        multi_person_tracker,
        ptz_controller = None
    ) -> np.ndarray:
        """
        Zeichnet alle getracken Personen mit IDs
        
        Args:
            frame: Input-Frame
            multi_person_tracker: MultiPersonTracker-Instanz
            ptz_controller: PTZ-Controller für Status-basierte Farben
        
        Returns:
            Frame mit allen getracken Personen
        """
        if multi_person_tracker is None:
            return frame
        
        if not config.SHOW_ALL_TRACKED_PERSONS:
            return frame
        
        # Alle Tracks holen
        tracks = multi_person_tracker.get_all_tracks()
        active_track_id = multi_person_tracker.active_track_id
        group_member_ids = multi_person_tracker.get_group_member_ids()
        
        for track in tracks:
            # Person ist "aktiv" wenn:
            # - Einzelmodus: track_id == active_track_id
            # - Gruppenmodus: track_id in group_frozen_track_ids
            is_active = (
                track.track_id == active_track_id or
                track.track_id in group_member_ids
            )
            
            # Für aktive Person(en): Geglättete Detection verwenden
            if is_active:
                detection = multi_person_tracker.get_active_detection()
                if detection is None:
                    detection = track.detection
            else:
                # Inaktive Personen: Ungeglättete Detection
                detection = track.detection
            
            # Farbe und Thickness basierend auf Status
            if is_active:
                # Aktive Person: Farbe abhängig von PTZ-Tracking Status
                ptz_enabled = ptz_controller is not None and ptz_controller.is_enabled()
                color = (0, 255, 255) if ptz_enabled else (255, 255, 255)  # Gelb wenn ON, Weiß wenn OFF
                thickness = 10 if ptz_enabled else 3
                corner_length = 60 if ptz_enabled else 20
            else:
                # Inaktive Personen: Grau
                color = config.INACTIVE_PERSON_COLOR
                thickness = 2
                corner_length = 20
            
            # Kopf-BBox zeichnen (basierend auf Gesichts-Features)
            head_bbox = detection.get_head_bbox(confidence_threshold=config.KEYPOINT_CONFIDENCE_THRESHOLD)
            
            if head_bbox is not None:
                # Kopf-BBox Ecken zeichnen
                self.draw_bbox_corners(
                    frame,
                    head_bbox[0], head_bbox[1],
                    head_bbox[2], head_bbox[3],
                    color,
                    thickness,
                    corner_length
                )
                
                # BBox-Zentrum für Label-Positionierung
                bbox_center_x = (head_bbox[0] + head_bbox[2]) // 2
                label_y = head_bbox[1]
            else:
                # Fallback: Ganzer Körper wenn keine Keypoints
                self.draw_bbox_corners(
                    frame,
                    detection.x1, detection.y1,
                    detection.x2, detection.y2,
                    color,
                    thickness,
                    corner_length
                )
                
                # BBox-Zentrum für Label-Positionierung
                bbox_center_x = (detection.x1 + detection.x2) // 2
                label_y = detection.y1
            
            # Label mit Track-ID oder GROUP
            # Im Gruppen-Tracking Modus: Zeige "GROUP" statt "PERSON: X"
            if is_active and multi_person_tracker.group_tracking_enabled:
                label = "GROUP"
            else:
                label = f"PERSON: {track.track_id}"
            
            if is_active and not ptz_enabled and not multi_person_tracker.group_tracking_enabled:
                label += " SELECTED"
            if is_active and ptz_enabled and not multi_person_tracker.group_tracking_enabled:
                label += " TRACKING"
            if is_active and ptz_enabled and multi_person_tracker.group_tracking_enabled:
                label += " TRACKING"
            
            label_size, _ = cv2.getTextSize(
                label,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                2
            )
            
            # Label horizontal zentrieren über BBox
            label_x = bbox_center_x - (label_size[0] + 10) // 2
            # Sicherstellen dass Label nicht über Bildrand hinausgeht
            label_x = max(0, label_x)
            label_x = min(label_x, frame.shape[1] - label_size[0] - 10)
            
            # Label-Farben basierend auf PTZ-Tracking Status (nur für aktive Person)
            if is_active:
                # Aktive Person: Farbe abhängig von PTZ-Tracking Status
                ptz_enabled = ptz_controller is not None and ptz_controller.is_enabled()
                label_bg_color = (0, 255, 255) if ptz_enabled else (255, 255, 255)  # Gelb wenn ON, Weiß wenn OFF
                label_text_color = (0, 0, 0)  # Immer Schwarz
            else:
                # Inaktive Personen: Grau/Weiß
                label_bg_color = color
                label_text_color = (255, 255, 255)
            
            # Label-Hintergrund
            cv2.rectangle(
                frame,
                (label_x, label_y - label_size[1] - 10),
                (label_x + label_size[0] + 10, label_y),
                label_bg_color,
                -1
            )
            
            # Label-Text
            cv2.putText(
                frame,
                label,
                (label_x + 5, label_y - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                label_text_color,
                2
            )
        
        return frame
    
    def draw_pose(
        self,
        frame: np.ndarray,
        detection: Optional[Detection]
    ) -> np.ndarray:
        """
        Zeichnet Pose-Keypoints und Skeleton auf Frame
        
        Args:
            frame: Input-Frame
            detection: Detection-Objekt mit Keypoints
        
        Returns:
            Frame mit gezeichneter Pose
        """
        if detection is None or not detection.has_pose():
            return frame
        
        if not config.ENABLE_POSE_ESTIMATION:
            return frame
        
        keypoints = detection.keypoints
        
        # Overlay für semi-transparente Pose erstellen
        overlay = frame.copy()
        
        # Skeleton zeichnen (Verbindungen zwischen Keypoints)
        if config.SHOW_SKELETON:
            for start_idx, end_idx in SKELETON_CONNECTIONS:
                # Prüfe ob beide Keypoints existieren
                if start_idx >= len(keypoints) or end_idx >= len(keypoints):
                    continue
                
                # Face-Features überspringen wenn deaktiviert (Keypoints 0-4: Nase, Augen, Ohren)
                if not config.SHOW_FACE_KEYPOINTS:
                    if start_idx <= 4 or end_idx <= 4:
                        continue
                
                start_kpt = keypoints[start_idx]
                end_kpt = keypoints[end_idx]
                
                # Prüfe Konfidenz
                if (start_kpt[2] < config.KEYPOINT_CONFIDENCE_THRESHOLD or
                    end_kpt[2] < config.KEYPOINT_CONFIDENCE_THRESHOLD):
                    continue
                
                # Koordinaten
                start_pos = (int(start_kpt[0]), int(start_kpt[1]))
                end_pos = (int(end_kpt[0]), int(end_kpt[1]))
                
                # Linie zeichnen (auf Overlay)
                cv2.line(
                    overlay,
                    start_pos,
                    end_pos,
                    config.SKELETON_COLOR,
                    config.SKELETON_THICKNESS,
                    lineType=cv2.LINE_AA
                )
        
        # Keypoints zeichnen (über Skeleton damit sie sichtbar bleiben)
        if config.SHOW_KEYPOINTS:
            for idx, kpt in enumerate(keypoints):
                x, y, conf = kpt
                
                # Face-Features überspringen wenn deaktiviert (Keypoints 0-4: Nase, Augen, Ohren)
                if not config.SHOW_FACE_KEYPOINTS and idx <= 4:
                    continue
                
                # Nur wenn Konfidenz hoch genug
                if conf < config.KEYPOINT_CONFIDENCE_THRESHOLD:
                    continue
                
                # Keypoint als Kreis zeichnen (auf Overlay)
                cv2.circle(
                    overlay,
                    (int(x), int(y)),
                    config.KEYPOINT_RADIUS,
                    config.KEYPOINT_COLOR,
                    -1,
                    lineType=cv2.LINE_AA
                )
                
                # Optional: kleiner schwarzer Rand für bessere Sichtbarkeit (auf Overlay)
                cv2.circle(
                    overlay,
                    (int(x), int(y)),
                    config.KEYPOINT_RADIUS,
                    (0, 0, 0),
                    1,
                    lineType=cv2.LINE_AA
                )
        
        # Overlay mit konfigurierbarer Transparenz auf Frame überblenden (Skeleton + Keypoints)
        if config.SHOW_SKELETON or config.SHOW_KEYPOINTS:
            cv2.addWeighted(overlay, config.POSE_OPACITY, frame, 1.0 - config.POSE_OPACITY, 0, frame)
        
        return frame
    
    def draw_info(
        self,
        frame: np.ndarray,
        detection: Optional[Detection] = None,
        ptz_controller = None
    ) -> np.ndarray:
        """
        Zeichnet Info-Overlay
        
        Args:
            frame: Input-Frame
            detection: Optional Detection für zusätzliche Infos
            ptz_controller: PTZ-Controller für Status-Anzeige
        
        Returns:
            Frame mit Info-Overlay
        """
        frame_height = frame.shape[0]
        y_offset = 60
        
        # System Stats (unten links, über FPS)
        if self.show_fps:
            sys_stats = self.system_stats.get_stats()
            stats_parts = [
                f"CPU: {sys_stats['process_cpu']:.0f}%",
                f"RAM: {sys_stats['process_ram_mb']:.0f}MB"
            ]
            
            # GPU hinzufügen falls verfügbar
            if sys_stats['gpu_name']:
                if sys_stats['gpu_mem_total_gb'] > 0:
                    # CUDA mit Total Memory
                    stats_parts.append(f"GPU: {sys_stats['gpu_mem_used_gb']:.1f}/{sys_stats['gpu_mem_total_gb']:.1f}GB")
                elif sys_stats['gpu_mem_used_gb'] > 0:
                    # MPS/CUDA mit nur Used Memory
                    stats_parts.append(f"GPU: {sys_stats['gpu_mem_used_gb']:.1f}GB")
                else:
                    # GPU aktiv aber kein Speicher-Tracking möglich
                    stats_parts.append(f"GPU: {sys_stats['gpu_name']}")
            
            stats_text = "  ".join(stats_parts)
            cv2.putText(
                frame,
                stats_text,
                (20, frame_height - 55),  # 30 Pixel über FPS
                cv2.FONT_HERSHEY_SIMPLEX,
                config.TEXT_SCALE,
                config.TEXT_COLOR,
                config.TEXT_THICKNESS
            )
        
        # FPS und PTZ Speeds (unten links, in einer Zeile)
        bottom_y = frame_height - 25  # 10 mehr vom unteren Rand
        info_parts = []
        
        # FPS
        if self.show_fps:
            fps = self.fps_counter.get_fps()
            info_parts.append(f"FPS: {fps:.1f}")
        
        # PTZ Speeds - nur wenn PTZ aktiv
        if ptz_controller is not None and ptz_controller.is_enabled():
            status = ptz_controller.get_status()
            # Normalisiere Speeds: 50 = Stop = 0, 1 = -49, 99 = +49
            pan_normalized = status["current_pan_speed"] - config.PTZ_SPEED_STOP
            tilt_normalized = status["current_tilt_speed"] - config.PTZ_SPEED_STOP
            info_parts.append(f"Pan: {pan_normalized:+3d}  Tilt: {tilt_normalized:+3d}")
        
        # Kombinierte Info-Zeile zeichnen
        if info_parts:
            info_text = "  |  ".join(info_parts)
            cv2.putText(
                frame,
                info_text,
                (20, bottom_y),  # 10 mehr von links
                cv2.FONT_HERSHEY_SIMPLEX,
                config.TEXT_SCALE,
                config.TEXT_COLOR,
                config.TEXT_THICKNESS
            )
        
        # PTZ-Status (prominent anzeigen - rechts oben)
        if ptz_controller is not None:
            ptz_enabled = ptz_controller.is_enabled()
            ptz_text = "Tracking: ON" if ptz_enabled else "Tracking: OFF"
            ptz_color = (0, 255, 255) if ptz_enabled else (255, 255, 255)  # Gelb/Rot
            
            # Text-Größe berechnen für rechts-Positionierung
            text_size, _ = cv2.getTextSize(
                ptz_text,
                cv2.FONT_HERSHEY_SIMPLEX,
                config.TEXT_SCALE * 1.2,
                config.TEXT_THICKNESS + 1
            )
            text_x = frame.shape[1] - text_size[0] - 20
            
            # Größerer Text für PTZ-Status
            cv2.putText(
                frame,
                ptz_text,
                (text_x, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                config.TEXT_SCALE * 1.2,  # Größer
                ptz_color,
                config.TEXT_THICKNESS + 1  # Dicker
            )
            y_offset += 35
        
        # Tracking-Info
        if self.show_info and detection:
            info_lines = [
                # f"Center: ({detection.center[0]}, {detection.center[1]})",
                # f"Size: {detection.width}x{detection.height}",
                # f"Area: {detection.area}px",
            ]
            
            for line in info_lines:
                cv2.putText(
                    frame,
                    line,
                    (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    config.TEXT_SCALE * 0.8,
                    config.TEXT_COLOR,
                    1
                )
                y_offset += 25
        
        return frame
    
    def draw_headroom_guide(
        self,
        frame: np.ndarray,
        detection: Optional[Detection] = None,
        ptz_controller = None,
        multi_person_tracker = None
    ) -> np.ndarray:
        """
        Zeichnet Headroom-Visualisierung und Tracking-Modus
        
        Zeigt die Soll-Position für die BBox-Oberkante (PTZ_HEADROOM)
        und die aktuelle Position an.
        
        Args:
            frame: Input-Frame
            detection: Optional Detection für aktuelle BBox-Position
            ptz_controller: PTZ-Controller (aktuell nicht verwendet)
            multi_person_tracker: MultiPersonTracker für Tracking-Modus-Anzeige
        
        Returns:
            Frame mit Headroom-Guide
        """
        frame_height, frame_width = frame.shape[:2]
        
        # Soll-Position berechnen (Headroom vom oberen Rand)
        target_y = int(frame_height * config.PTZ_HEADROOM)
        
        # Deadzone berechnen
        deadzone_pixels = int(frame_height * config.PTZ_DEADZONE_Y)
        deadzone_top = max(0, target_y - deadzone_pixels)
        deadzone_bottom = min(frame_height, target_y + deadzone_pixels)
        
        # Deadzone als semi-transparenter Bereich (optional)
        if config.SHOW_HEADROOM_LINE_DEADZONE:
            overlay = frame.copy()
            cv2.rectangle(
                overlay,
                (0, deadzone_top),
                (frame_width, deadzone_bottom),
                (255, 255, 255),  # Weiß
                -1
            )
            # Mit Transparenz überblenden
            cv2.addWeighted(overlay, 0.1, frame, 0.9, 0, frame)
        
        # Farbe für Headroom-Elemente
        line_color = (255, 255, 255)  # Weiß
        
        # Soll-Position: horizontale Linie (gestrichelt) - nur wenn aktiviert
        if config.SHOW_HEADROOM_LINE:
            overlay = frame.copy()
            dash_length = 4
            gap_length = 15

            padding: int = int(frame_width/4)  # Abstand von der Linie zu den Enden
            
            x = 0 + padding
            while x < frame_width - padding:
                x_end = min(x + dash_length, frame_width - padding)
                cv2.line(
                    overlay,
                    (x, target_y),
                    (x_end, target_y),
                    line_color,
                    4,
                    lineType=cv2.LINE_AA
                )
                x += dash_length + gap_length
            cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
        # Headroom-Wert anzeigen (links oben)
        headroom_text = f"Headroom: {int(config.PTZ_HEADROOM * 100)}%"
        text_x = 20
        text_y = 60
        
        # Text
        cv2.putText(
            frame,
            headroom_text,
            (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            config.TEXT_SCALE * 1.2,
            line_color,
            2,
            lineType=cv2.LINE_AA
        )
        
        # Wenn Detection vorhanden: aktuelle BBox-Oberkante markieren
        if detection is not None and config.SHOW_HEADROOM_LINE_ON_PERSON:
            bbox_top_y = detection.y1
            
            # Aktuelle Position als durchgezogene Linie (nur in Bildmitte)
            bbox_line_color = (0, 0, 255)  # Rot wenn zu weit von Soll entfernt
            
            # Abweichung berechnen
            deviation = abs(bbox_top_y - target_y)
            if deviation <= deadzone_pixels:
                bbox_line_color = (0, 255, 0)  # Grün wenn in Deadzone
            elif deviation <= deadzone_pixels * 2:
                bbox_line_color = (0, 255, 255)  # Gelb wenn nahe
            
            # Linie mit fixer Breite von 10% Bildbreite (zentriert über Nase oder BBox-Center)
            line_width = int(frame_width * 0.1)
            
            # Versuche Nase-Position zu verwenden (Keypoint 0)
            center_x = (detection.x1 + detection.x2) // 2  # Fallback: BBox-Center
            if detection.has_pose() and len(detection.keypoints) > 0:
                nose = detection.keypoints[0]  # Keypoint 0 = Nase
                if nose[2] >= config.KEYPOINT_CONFIDENCE_THRESHOLD:
                    center_x = int(nose[0])
            
            line_start_x = max(0, center_x - line_width // 2)
            line_end_x = min(frame_width, center_x + line_width // 2)
            
            cv2.line(
                frame,
                (line_start_x, bbox_top_y),
                (line_end_x, bbox_top_y),
                bbox_line_color,
                2,
                lineType=cv2.LINE_AA
            )
            
            # Kleine Marker an den Enden
            # cv2.circle(frame, (line_start_x, bbox_top_y), 4, bbox_line_color, -1)
            # cv2.circle(frame, (line_end_x, bbox_top_y), 4, bbox_line_color, -1)
            
            # Abweichung anzeigen (als Text neben der Linie)
            # deviation_percent = deviation / frame_height
            # deviation_text = f"{deviation_percent:.1%}"
            
            # cv2.putText(
            #     frame,
            #     deviation_text,
            #     (line_end_x + 10, bbox_top_y + 5),
            #     cv2.FONT_HERSHEY_SIMPLEX,
            #     0.5,
            #     bbox_line_color,
            #     2,
            #     lineType=cv2.LINE_AA
            # )
        
        return frame
    
    def show(
        self,
        frame: np.ndarray,
        detection: Optional[Detection] = None,
        ptz_controller = None,
        multi_person_tracker = None
    ) -> int:
        """
        Zeigt Frame mit Visualisierung an
        
        Args:
            frame: Input-Frame
            detection: Optional Detection zum Zeichnen (aktive Person)
            ptz_controller: PTZ-Controller für Status-Anzeige
            multi_person_tracker: MultiPersonTracker für alle Personen
        
        Returns:
            Gedrückte Taste (oder -1)
        """
        # Window erstellen falls nötig
        if not self.window_created:
            self.create_window()
        
        # FPS aktualisieren
        self.fps_counter.update()
        
        # Frame kopieren für Visualisierung
        display_frame = frame.copy()
        
        # 1. Headroom-Guide zeichnen (Hintergrund - Deadzone + Linie)
        display_frame = self.draw_headroom_guide(display_frame, detection, ptz_controller, multi_person_tracker)
        
        # 2. Multi-Person-Tracking zeichnen (alle Personen mit BBoxen)
        if multi_person_tracker is not None:
            display_frame = self.draw_multi_person_tracking(display_frame, multi_person_tracker, ptz_controller)
        else:
            # Fallback: nur aktive Detection zeichnen
            display_frame = self.draw_detection(display_frame, detection)
        
        # 3. Pose zeichnen (Keypoints und Skeleton) - nur für aktive Person
        display_frame = self.draw_pose(display_frame, detection)
        
        # 4. Info-Overlay (Vordergrund)
        display_frame = self.draw_info(display_frame, detection, ptz_controller)
        
        # Resize für Display
        if display_frame.shape[1] != self.display_size[0] or display_frame.shape[0] != self.display_size[1]:
            display_frame = cv2.resize(display_frame, self.display_size)
        
        # Anzeigen
        cv2.imshow(self.window_name, display_frame)
        
        # Key-Events
        key = cv2.waitKey(1) & 0xFF
        
        return key
    
    def destroy(self):
        """
        Schließt Window
        """
        if self.window_created:
            cv2.destroyWindow(self.window_name)
            self.window_created = False
            logger.info("Window geschlossen")
    
    def __enter__(self):
        """Context Manager Support"""
        self.create_window()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager Support"""
        self.destroy()
        return False


if __name__ == "__main__":
    # Test
    logger.info("Testing Visualizer...")
    
    # Dummy-Frame
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    
    # Dummy-Detection
    detection = Detection(
        bbox=(300, 200, 600, 650),
        confidence=0.95
    )
    
    with Visualizer() as viz:
        for i in range(100):
            key = viz.show(frame, detection)
            
            if key == ord('q'):
                break
    
    logger.info("Test abgeschlossen")
