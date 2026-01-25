"""
城市固废智能监测系统
=====================

基于卫星遥感影像的城市固体废物智能检测和综合监管系统。

功能特点:
- 支持两种运行模式：测试模式（大图切割）和生产模式（小图直接处理）
- 双API模型协作：大模型初筛 + 小模型精检
- 串行处理：稳定可靠的逐图处理流程
- 综合报告：集成搜索、天气、历史数据生成监管报告

使用示例:

```python
import asyncio
from swagent.waste_monitoring import run_waste_monitoring, RunMode

# 测试模式
result = asyncio.run(run_waste_monitoring(
    mode=RunMode.TEST,
    input_path="/path/to/large_image.tif",
    city_name="北京市",
    tile_size=512,
    tile_overlap=64,
    output_dir="./output"
))

# 生产模式
result = asyncio.run(run_waste_monitoring(
    mode=RunMode.PRODUCTION,
    input_path="/path/to/tiles_directory/",
    city_name="北京市",
    output_dir="./output"
))

print(f"确认堆存点: {result.confirmed_count}")
print(f"报告路径: {result.report_path}")
```

命令行使用:

```bash
# 测试模式
python -m swagent.waste_monitoring --mode test --input /path/to/image.tif --city "北京市"

# 生产模式
python -m swagent.waste_monitoring --mode prod --input /path/to/tiles/ --city "北京市"
```
"""

from .state import (
    RunMode,
    Classification,
    TileResult,
    WasteMonitoringState,
    create_initial_state,
)

from .runner import (
    MonitoringResult,
    run_waste_monitoring,
    run_test_mode,
    run_production_mode,
    run_sync,
)

from .workflow import create_waste_monitoring_workflow

__all__ = [
    # State
    "RunMode",
    "Classification",
    "TileResult",
    "WasteMonitoringState",
    "create_initial_state",
    # Runner
    "MonitoringResult",
    "run_waste_monitoring",
    "run_test_mode",
    "run_production_mode",
    "run_sync",
    # Workflow
    "create_waste_monitoring_workflow",
]

__version__ = "0.1.0"
