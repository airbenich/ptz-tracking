#!/usr/bin/env python3
"""
Multi-Person Tracking Beispiel
Zeigt wie man mit mehreren Personen tracken kann
"""

import sys
from pathlib import Path

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tracking.person_detector import PersonDetector, Detection
from src.tracking.multi_person_tracker import MultiPersonTracker
from src import config


def main():
    """Beispiel für Multi-Person-Tracking"""
    
    print("=" * 60)
    print("Multi-Person Tracking Beispiel")
    print("=" * 60)
    
    # Multi-Person-Tracker erstellen
    tracker = MultiPersonTracker(
        max_distance_threshold=150,  # Max. Distanz für Track-Zuordnung
        smoothing_enabled=True,
        smoothing_factor=0.3
    )
    
    # Simuliere mehrere Frames mit Detections
    
    # Frame 1: Drei Personen erkannt
    print("\n--- Frame 1 ---")
    detections1 = [
        Detection(bbox=(100, 100, 300, 500), confidence=0.9),   # Person 1
        Detection(bbox=(400, 150, 600, 550), confidence=0.8),   # Person 2
        Detection(bbox=(700, 200, 850, 600), confidence=0.7),   # Person 3
    ]
    
    tracked = tracker.update(detections1, (720, 1280, 3))
    print(f"Getrackte Personen: {len(tracker.get_all_tracks())}")
    print(f"Aktive Person: {tracker.active_track_id}")
    print(f"Tracked Detection: {tracked}")
    
    # Status ausgeben
    status = tracker.get_status()
    print(f"\nStatus:")
    for track in status['tracks']:
        print(f"  - ID {track['track_id']}: Center {track['center']}, Area {track['area']}px²")
    
    # Frame 2: Personen bewegen sich
    print("\n--- Frame 2 ---")
    detections2 = [
        Detection(bbox=(110, 105, 310, 505), confidence=0.9),   # Person 1 (leicht bewegt)
        Detection(bbox=(410, 155, 610, 555), confidence=0.8),   # Person 2 (leicht bewegt)
        Detection(bbox=(710, 205, 860, 605), confidence=0.7),   # Person 3 (leicht bewegt)
    ]
    
    tracked = tracker.update(detections2, (720, 1280, 3))
    print(f"Getrackte Personen: {len(tracker.get_all_tracks())}")
    print(f"Aktive Person: {tracker.active_track_id}")
    
    # Frame 3: Eine Person verschwindet
    print("\n--- Frame 3 ---")
    detections3 = [
        Detection(bbox=(120, 110, 320, 510), confidence=0.9),   # Person 1
        Detection(bbox=(720, 210, 870, 610), confidence=0.7),   # Person 3
        # Person 2 ist nicht mehr sichtbar
    ]
    
    tracked = tracker.update(detections3, (720, 1280, 3))
    print(f"Getrackte Personen: {len(tracker.get_all_tracks())}")
    print(f"Aktive Person: {tracker.active_track_id}")
    
    # Manuell zur nächsten Person wechseln
    print("\n--- Manueller Wechsel ---")
    new_id = tracker.select_next_person()
    print(f"Gewechselt zu Person ID: {new_id}")
    
    tracked = tracker.get_active_detection()
    print(f"Neue aktive Detection: {tracked}")
    
    # Nochmal wechseln (loop)
    new_id = tracker.select_next_person()
    print(f"Gewechselt zu Person ID: {new_id}")
    
    # Spezifische Person auswählen
    print("\n--- Spezifische Person auswählen ---")
    success = tracker.select_person_by_id(1)
    print(f"Person 1 ausgewählt: {success}")
    print(f"Aktive Person: {tracker.active_track_id}")
    
    # Versuche nicht-existierende Person
    success = tracker.select_person_by_id(99)
    print(f"Person 99 ausgewählt: {success} (existiert nicht)")
    
    print("\n" + "=" * 60)
    print("Multi-Person Tracking Beispiel abgeschlossen")
    print("=" * 60)


if __name__ == "__main__":
    main()
