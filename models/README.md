# Modelle

## YOLO Modelle

Dieses Verzeichnis enthält die YOLO-Modelle für Person Detection.

### Download

Die Modelle werden beim ersten Start automatisch heruntergeladen:
- `yolov8n.pt` - Nano (schnellste, ca. 6 MB)
- `yolov8s.pt` - Small (ca. 22 MB)
- `yolov8m.pt` - Medium (ca. 50 MB)
- `yolov8l.pt` - Large (ca. 88 MB)
- `yolov8x.pt` - Extra Large (beste Genauigkeit, ca. 136 MB)

### Empfehlung

Für Echtzeit-Performance: **yolov8n.pt** oder **yolov8s.pt**

### Manueller Download

```bash
pip install ultralytics
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```
