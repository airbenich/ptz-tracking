"""
Performance-Messung und FPS-Counter
Utility für Echtzeit-Performance-Monitoring
"""

import time
import psutil
from collections import deque
from typing import Optional

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class FPSCounter:
    """
    Echtzeit FPS-Counter mit gleitender Durchschnittsberechnung
    """
    
    def __init__(self, buffer_size: int = 30):
        """
        Args:
            buffer_size: Anzahl der Frames für Durchschnittsberechnung
        """
        self.buffer_size = buffer_size
        self.frame_times = deque(maxlen=buffer_size)
        self.start_time = time.time()
        self.frame_count = 0
        self.last_frame_time = time.time()
    
    def update(self):
        """
        Aktualisiert den FPS-Counter mit neuem Frame
        """
        current_time = time.time()
        frame_time = current_time - self.last_frame_time
        self.frame_times.append(frame_time)
        self.last_frame_time = current_time
        self.frame_count += 1
    
    def get_fps(self) -> float:
        """
        Berechnet aktuelle FPS (gleitender Durchschnitt)
        
        Returns:
            FPS als Float
        """
        if not self.frame_times:
            return 0.0
        
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        
        if avg_frame_time > 0:
            return 1.0 / avg_frame_time
        return 0.0
    
    def get_average_fps(self) -> float:
        """
        Berechnet durchschnittliche FPS über gesamte Laufzeit
        
        Returns:
            Durchschnittliche FPS
        """
        elapsed_time = time.time() - self.start_time
        
        if elapsed_time > 0:
            return self.frame_count / elapsed_time
        return 0.0
    
    def get_frame_count(self) -> int:
        """
        Returns:
            Anzahl verarbeiteter Frames
        """
        return self.frame_count
    
    def get_elapsed_time(self) -> float:
        """
        Returns:
            Vergangene Zeit in Sekunden
        """
        return time.time() - self.start_time
    
    def reset(self):
        """
        Setzt den Counter zurück
        """
        self.frame_times.clear()
        self.start_time = time.time()
        self.frame_count = 0
        self.last_frame_time = time.time()
    
    def __str__(self) -> str:
        """
        String-Repräsentation für einfache Ausgabe
        """
        return f"FPS: {self.get_fps():.1f} (Avg: {self.get_average_fps():.1f})"


class PerformanceMonitor:
    """
    Erweiterte Performance-Überwachung mit mehreren Metriken
    """
    
    def __init__(self):
        self.fps_counter = FPSCounter()
        self.timers = {}
        self.counters = {}
    
    def start_timer(self, name: str):
        """
        Startet einen benannten Timer
        
        Args:
            name: Name des Timers
        """
        self.timers[name] = time.time()
    
    def stop_timer(self, name: str) -> Optional[float]:
        """
        Stoppt einen benannten Timer und gibt die Dauer zurück
        
        Args:
            name: Name des Timers
        
        Returns:
            Dauer in Sekunden oder None wenn Timer nicht existiert
        """
        if name not in self.timers:
            return None
        
        duration = time.time() - self.timers[name]
        del self.timers[name]
        return duration
    
    def increment_counter(self, name: str, value: int = 1):
        """
        Inkrementiert einen benannten Counter
        
        Args:
            name: Name des Counters
            value: Wert um den inkrementiert wird
        """
        if name not in self.counters:
            self.counters[name] = 0
        self.counters[name] += value
    
    def get_counter(self, name: str) -> int:
        """
        Holt den Wert eines Counters
        
        Args:
            name: Name des Counters
        
        Returns:
            Counter-Wert oder 0 wenn nicht existiert
        """
        return self.counters.get(name, 0)
    
    def reset_counter(self, name: str):
        """
        Setzt einen Counter zurück
        
        Args:
            name: Name des Counters
        """
        if name in self.counters:
            self.counters[name] = 0
    
    def update_fps(self):
        """
        Aktualisiert FPS-Counter
        """
        self.fps_counter.update()
    
    def get_fps(self) -> float:
        """
        Returns:
            Aktuelle FPS
        """
        return self.fps_counter.get_fps()
    
    def get_stats(self) -> dict:
        """
        Gibt alle Performance-Statistiken zurück
        
        Returns:
            Dictionary mit allen Metriken
        """
        return {
            'fps': self.fps_counter.get_fps(),
            'avg_fps': self.fps_counter.get_average_fps(),
            'frame_count': self.fps_counter.get_frame_count(),
            'elapsed_time': self.fps_counter.get_elapsed_time(),
            'counters': self.counters.copy()
        }
    
    def reset(self):
        """
        Setzt alle Metriken zurück
        """
        self.fps_counter.reset()
        self.timers.clear()
        self.counters.clear()
    
    def __str__(self) -> str:
        """
        String-Repräsentation
        """
        lines = [str(self.fps_counter)]
        
        if self.counters:
            lines.append("Counters:")
            for name, value in self.counters.items():
                lines.append(f"  {name}: {value}")
        
        return "\n".join(lines)


class Timer:
    """
    Context-Manager für einfache Zeitmessung
    
    Verwendung:
        with Timer("operation_name") as t:
            # Code hier
            pass
        print(f"Dauer: {t.duration:.3f}s")
    """
    
    def __init__(self, name: str = "Timer", print_on_exit: bool = False):
        """
        Args:
            name: Name des Timers (für Ausgabe)
            print_on_exit: Automatisch Zeit ausgeben beim Beenden
        """
        self.name = name
        self.print_on_exit = print_on_exit
        self.start_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = time.time() - self.start_time
        
        if self.print_on_exit:
            print(f"{self.name}: {self.duration:.3f}s")
        
        return False


class SystemStats:
    """
    System-Performance-Statistiken für Tracking
    """
    
    def __init__(self):
        """Initialisiert System-Stats-Monitor"""
        self.process = psutil.Process()
        
        # GPU-Info initialisieren
        self.has_mps = TORCH_AVAILABLE and torch.backends.mps.is_available()
        self.has_cuda = TORCH_AVAILABLE and torch.cuda.is_available()
    
    def get_stats(self) -> dict:
        """
        Holt relevante System-Statistiken
        
        Returns:
            Dict mit CPU, RAM, etc.
        """
        try:
            # CPU-Auslastung (Prozent)
            cpu_percent = self.process.cpu_percent(interval=0)
            
            # RAM-Nutzung
            mem_info = self.process.memory_info()
            mem_mb = mem_info.rss / (1024 * 1024)  # In MB
            
            # System-weite Stats
            system_cpu = psutil.cpu_percent(interval=0)
            system_mem = psutil.virtual_memory().percent
            
            # GPU-Stats
            gpu_name = None
            gpu_mem_used = 0.0
            gpu_mem_total = 0.0
            
            if self.has_cuda:
                try:
                    gpu_mem_used = torch.cuda.memory_allocated() / (1024**3)  # GB
                    gpu_mem_total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                    gpu_name = 'CUDA'
                except Exception:
                    pass
            elif self.has_mps:
                try:
                    # MPS: Verwende driver_allocated_memory für bessere Genauigkeit
                    # current_allocated_memory zeigt nur PyTorch-Tensoren
                    # driver_allocated_memory zeigt den tatsächlichen Speicher
                    if hasattr(torch.mps, 'driver_allocated_memory'):
                        gpu_mem_used = torch.mps.driver_allocated_memory() / (1024**3)  # GB
                    else:
                        gpu_mem_used = torch.mps.current_allocated_memory() / (1024**3)  # GB
                    gpu_name = 'MPS'
                    # MPS hat keinen total memory API
                    gpu_mem_total = 0.0
                except Exception:
                    # Fallback: Zeige nur dass MPS aktiv ist
                    gpu_name = 'MPS'
                    gpu_mem_used = 0.0
                    gpu_mem_total = 0.0
            
            return {
                'process_cpu': cpu_percent,
                'process_ram_mb': mem_mb,
                'system_cpu': system_cpu,
                'system_ram': system_mem,
                'gpu_name': gpu_name,
                'gpu_mem_used_gb': gpu_mem_used,
                'gpu_mem_total_gb': gpu_mem_total,
            }
        except Exception:
            return {
                'process_cpu': 0.0,
                'process_ram_mb': 0.0,
                'system_cpu': 0.0,
                'system_ram': 0.0,
                'gpu_name': None,
                'gpu_mem_used_gb': 0.0,
                'gpu_mem_total_gb': 0.0,
            }


if __name__ == "__main__":
    # Test FPS-Counter
    print("Testing FPS Counter...")
    print("-" * 60)
    
    fps = FPSCounter(buffer_size=10)
    
    # Simuliere 30 FPS
    for i in range(50):
        time.sleep(1/30)  # ~33ms pro Frame
        fps.update()
        
        if (i + 1) % 10 == 0:
            print(f"Frame {i+1}: {fps}")
    
    print("-" * 60)
    
    # Test Performance Monitor
    print("\nTesting Performance Monitor...")
    print("-" * 60)
    
    monitor = PerformanceMonitor()
    
    # Simuliere verschiedene Operationen
    for i in range(20):
        monitor.start_timer("frame_processing")
        time.sleep(0.02)  # Simuliere Processing
        duration = monitor.stop_timer("frame_processing")
        
        monitor.update_fps()
        monitor.increment_counter("processed_frames")
        
        if i % 5 == 0:
            monitor.increment_counter("detections", 2)
    
    print(monitor)
    print("\nStats:", monitor.get_stats())
    print("-" * 60)
    
    # Test Timer Context Manager
    print("\nTesting Timer Context Manager...")
    print("-" * 60)
    
    with Timer("Test Operation", print_on_exit=True):
        time.sleep(0.1)
    
    print("-" * 60)
    print("Performance-Tests abgeschlossen")
