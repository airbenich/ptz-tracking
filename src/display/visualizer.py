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
            for kpt in keypoints:
                x, y, conf = kpt
                
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
        
        # PTZ-Status (prominent anzeigen)
        if ptz_controller is not None:
            ptz_enabled = ptz_controller.is_enabled()
            ptz_text = "Tracking: ON" if ptz_enabled else "Tracking: OFF"
            ptz_color = (0, 255, 255) if ptz_enabled else (255, 255, 255)  # Gelb/Rot
            
            # Größerer Text für PTZ-Status
            cv2.putText(
                frame,
                ptz_text,
                (20, y_offset),
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
        ptz_controller = None
    ) -> np.ndarray:
        """
        Zeichnet Headroom-Visualisierung
        
        Zeigt die Soll-Position für die BBox-Oberkante (PTZ_HEADROOM)
        und die aktuelle Position an.
        
        Args:
            frame: Input-Frame
            detection: Optional Detection für aktuelle BBox-Position
            ptz_controller: PTZ-Controller (aktuell nicht verwendet)
        
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
        
        # Soll-Position: horizontale Linie (gestrichelt)
        line_color = (255, 255, 255)  # Weiß
        dash_length = 20
        gap_length = 10
        
        x = 0
        while x < frame_width:
            x_end = min(x + dash_length, frame_width)
            cv2.line(
                frame,
                (x, target_y),
                (x_end, target_y),
                line_color,
                2,
                lineType=cv2.LINE_AA
            )
            x += dash_length + gap_length
        
        # Headroom-Wert anzeigen (rechts oben)
        headroom_text = f"Headroom: {int(config.PTZ_HEADROOM * 100)}%"
        text_size, _ = cv2.getTextSize(
            headroom_text,
            cv2.FONT_HERSHEY_SIMPLEX,
            config.TEXT_SCALE * 1.2,
            2
        )
        text_x = frame_width - text_size[0] - 20
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
        if detection is not None:
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
        ptz_controller = None
    ) -> int:
        """
        Zeigt Frame mit Visualisierung an
        
        Args:
            frame: Input-Frame
            detection: Optional Detection zum Zeichnen
            ptz_controller: PTZ-Controller für Status-Anzeige
        
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
        
        # Detection zeichnen
        display_frame = self.draw_detection(display_frame, detection)
        
        # Pose zeichnen (Keypoints und Skeleton)
        display_frame = self.draw_pose(display_frame, detection)
        
        # Headroom-Guide zeichnen
        display_frame = self.draw_headroom_guide(display_frame, detection, ptz_controller)
        
        # Info-Overlay
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
