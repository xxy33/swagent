"""Web application configuration."""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "output"

# Ensure directories exist
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Server settings
HOST = os.getenv("WEB_HOST", "0.0.0.0")
PORT = int(os.getenv("WEB_PORT", "8080"))

# Upload settings
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB per file
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}

# Detection tasks - IDs must match task_prompts.yaml
DETECTION_TASKS = [
    {
        "id": "aerial_waste",
        "name": "非法堆存检测",
        "name_en": "Illegal Dumping Detection",
        "description": "检测航拍图像中的非法堆存物"
    },
    {
        "id": "cwld",
        "name": "建筑垃圾检测",
        "name_en": "Construction Waste Detection",
        "description": "检测建筑垃圾堆放区域"
    },
    {
        "id": "landfill",
        "name": "填埋场检测",
        "name_en": "Landfill Detection",
        "description": "检测和分析垃圾填埋场"
    },
    {
        "id": "solar_photovoltaic_arrays",
        "name": "光伏检测",
        "name_en": "Solar Photovoltaic Detection",
        "description": "检测太阳能光伏板和阵列"
    },
    {
        "id": "wind_turbines",
        "name": "风机检测",
        "name_en": "Wind Turbine Detection",
        "description": "检测风力发电涡轮机"
    },
    {
        "id": "tank",
        "name": "储罐检测",
        "name_en": "Storage Tank Detection",
        "description": "检测各类储罐设施"
    }
]
