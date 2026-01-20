# GIS Agent 工具使用指南

本文档介绍如何使用新增的 GIS 相关工具：天气查询工具（WeatherTool）和影像切片工具（ImageryTool）。

## 工具概述

### 1. WeatherTool - 天气查询工具

根据 GIS 坐标（纬度、经度）和时间查询天气数据。

**数据源**: Open-Meteo API
**支持功能**:
- 查询当前天气
- 查询指定时间的天气（历史/预报）
- 自定义时区
- 返回温度、湿度、降水量、风速等信息

### 2. ImageryTool - 影像切片工具

根据 GIS 坐标获取卫星影像数据。

**数据源**:
- **Google Earth**: 高清卫星图（静态）
- **吉林一号 (JL1)**: 国产卫星图（支持 2022、2023、2024 年份）
- **Sentinel-2**: 哨兵2号卫星图（支持时间筛选和云量过滤）

**支持功能**:
- 点位模式：指定中心点坐标 [lon, lat]
- 区域模式：指定矩形区域 [min_lon, min_lat, max_lon, max_lat]
- 可配置缩放级别、图片大小等参数
- 返回 numpy 数组或 base64 编码图片

## 安装依赖

```bash
# 基础依赖
pip install requests pillow numpy mercantile

# 如果使用 Sentinel-2，还需要安装:
pip install earthengine-api geemap pandas
```

## 快速开始

### 1. 直接使用天气工具

```python
import asyncio
from swagent.tools.domain import WeatherTool

async def query_weather():
    weather_tool = WeatherTool()

    # 查询当前天气
    result = await weather_tool.safe_execute(
        latitude=39.9042,
        longitude=116.4074
    )

    if result.success:
        print(f"天气数据: {result.data['data']}")
    else:
        print(f"查询失败: {result.error}")

asyncio.run(query_weather())
```

### 2. 直接使用影像切片工具

```python
import asyncio
from swagent.tools.domain import ImageryTool

async def query_imagery():
    imagery_tool = ImageryTool()

    # 查询 Google Earth 影像
    result = await imagery_tool.safe_execute(
        location=[116.4074, 39.9042],  # 北京
        source="google",
        zoom_level=18,
        point_size=1000
    )

    if result.success:
        print(f"影像形状: {result.data['shape']}")
        print(f"数组信息: {result.data['array_info']}")
    else:
        print(f"查询失败: {result.error}")

asyncio.run(query_imagery())
```

### 3. 使用工具注册中心

```python
import asyncio
from swagent.tools import ToolRegistry
from swagent.tools.domain import WeatherTool, ImageryTool

async def use_registry():
    # 创建工具注册中心
    registry = ToolRegistry()

    # 注册工具
    registry.register(WeatherTool())
    registry.register(ImageryTool())

    # 通过注册中心执行
    result = await registry.execute_tool(
        "weather_query",
        latitude=39.9042,
        longitude=116.4074
    )

    print(result.data)

asyncio.run(use_registry())
```

### 4. 结合 Agent 使用

```python
import asyncio
from swagent.agents import ReActAgent
from swagent.llm import OpenAIClient, LLMConfig
from swagent.tools import ToolRegistry
from swagent.tools.domain import WeatherTool, ImageryTool

async def use_with_agent():
    # 配置 LLM
    config = LLMConfig(
        provider="openai",
        model="gpt-4",
        api_key="your-api-key"
    )
    llm = OpenAIClient(config)

    # 创建工具注册中心
    registry = ToolRegistry()
    registry.register(WeatherTool())
    registry.register(ImageryTool())

    # 创建 Agent
    agent = ReActAgent(
        name="GIS助手",
        llm=llm,
        tools=registry.get_all_tools()
    )

    # 执行任务
    task = "请查询北京（39.9042, 116.4074）的当前天气，并获取该位置的卫星影像信息"
    result = await agent.execute(task)
    print(result)

asyncio.run(use_with_agent())
```

## API 参数说明

### WeatherTool 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| latitude | number | 是 | - | 纬度（-90 到 90） |
| longitude | number | 是 | - | 经度（-180 到 180） |
| when | string | 否 | None | 查询时间，ISO8601 格式（如 '2026-01-20T14:00'） |
| timezone | string | 否 | "Asia/Shanghai" | 时区 |

**返回数据示例**:

```json
{
  "mode": "current",
  "data": {
    "time": "2026-01-20T14:00",
    "temperature_2m": 5.2,
    "relative_humidity_2m": 45,
    "precipitation": 0.0,
    "wind_speed_10m": 3.5
  }
}
```

### ImageryTool 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| location | array | 是 | - | 点位: [lon, lat]；区域: [min_lon, min_lat, max_lon, max_lat] |
| source | string | 是 | - | 数据源: "google", "jilin", "sentinel" |
| zoom_level | number | 否 | 18 | 缩放级别（Google/Jilin），18≈0.6m，19≈0.3m |
| point_size | number | 否 | 2000 | 点位模式下的图片大小（Google/Jilin） |
| year | number | 否 | 2024 | 年份（Jilin），支持 2022, 2023, 2024 |
| date_range | array | 否 | - | 日期范围（Sentinel），如 ["2023-01-01", "2023-01-31"] |
| bands | array | 否 | ["B4", "B3", "B2"] | 波段（Sentinel），默认 RGB |
| max_cloud_cover | number | 否 | 20 | 最大云量百分比（Sentinel） |
| return_format | string | 否 | "array" | 返回格式: "array" 或 "base64" |

**返回数据示例**:

```json
{
  "source": "google",
  "location": [116.4074, 39.9042],
  "shape": [1000, 1000, 3],
  "mode": "point",
  "zoom_level": 18,
  "array_info": {
    "dtype": "uint8",
    "min": 0,
    "max": 255,
    "mean": 127.5
  }
}
```

## 使用示例

### 示例 1: 查询指定时间的天气

```python
result = await weather_tool.safe_execute(
    latitude=39.9042,
    longitude=116.4074,
    when="2026-01-25T10:00",
    timezone="Asia/Shanghai"
)
```

### 示例 2: Google Earth 点位查询

```python
result = await imagery_tool.safe_execute(
    location=[116.4074, 39.9042],
    source="google",
    zoom_level=19,
    point_size=2000
)
```

### 示例 3: 吉林一号区域查询

```python
result = await imagery_tool.safe_execute(
    location=[116.35, 39.85, 116.45, 39.95],
    source="jilin",
    zoom_level=18,
    year=2024
)
```

### 示例 4: Sentinel-2 时序查询

```python
result = await imagery_tool.safe_execute(
    location=[116.397, 39.908],
    source="sentinel",
    date_range=["2023-05-01", "2023-09-01"],
    bands=["B4", "B3", "B2"],
    max_cloud_cover=10
)
```

### 示例 5: 获取 base64 编码图片

```python
result = await imagery_tool.safe_execute(
    location=[116.4074, 39.9042],
    source="google",
    zoom_level=18,
    point_size=1000,
    return_format="base64"
)

# 使用 base64 图片
img_base64 = result.data['image_base64']
# 可以直接在网页中显示: <img src="data:image/png;base64,{img_base64}" />
```

## 运行完整示例

```bash
# 运行 GIS Agent 示例
python examples/gis_agent_demo.py
```

该示例包含 4 个演示：
1. 直接使用天气工具
2. 直接使用影像切片工具
3. 使用工具注册中心
4. 结合 ReAct Agent 使用（需要配置 OPENAI_API_KEY）

## 注意事项

1. **网络连接**: 所有工具都需要网络连接来访问 API
2. **API 限制**:
   - Open-Meteo API 有请求频率限制
   - 影像下载可能需要较长时间，建议设置合适的超时时间
3. **Sentinel-2 配置**: 使用 Sentinel-2 前需要先在 Google Earth Engine 进行认证：
   ```python
   import ee
   ee.Authenticate()
   ee.Initialize(project='your-project-id')
   ```
4. **数据大小**: 下载大区域的影像数据可能占用较大内存，请根据实际情况调整参数

## 故障排除

### 问题 1: 天气查询失败

**可能原因**: 网络连接问题或 API 限制
**解决方案**: 检查网络连接，等待后重试

### 问题 2: Google/Jilin 影像下载失败

**可能原因**: 网络连接问题或坐标超出范围
**解决方案**:
- 检查坐标是否正确（经度 -180 到 180，纬度 -90 到 90）
- 检查网络连接
- 降低 zoom_level 或 point_size

### 问题 3: Sentinel-2 初始化失败

**可能原因**: 未进行 Google Earth Engine 认证
**解决方案**:
```bash
# 在终端运行
earthengine authenticate
# 按提示在浏览器完成认证
```

## 工具架构

```
swagent/tools/domain/
├── weather_tool.py       # 天气查询工具
├── imagery_tool.py       # 影像切片工具
└── __init__.py           # 导出工具

数据接口/
├── opts_google.py        # Google Earth 下载器
├── opts_jilin.py         # 吉林一号下载器
└── opts_sentinel.py      # Sentinel-2 处理器
```

## 扩展和自定义

你可以继承 `BaseTool` 类来创建自定义的 GIS 工具：

```python
from swagent.tools.base_tool import BaseTool, ToolCategory, ToolParameter, ToolResult

class MyCustomGISTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_gis_tool"

    @property
    def description(self) -> str:
        return "我的自定义 GIS 工具"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.DOMAIN

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="param1",
                type="string",
                description="参数1",
                required=True
            )
        ]

    def get_return_description(self) -> str:
        return "返回处理结果"

    async def execute(self, **kwargs) -> ToolResult:
        # 实现你的逻辑
        return ToolResult(success=True, data={"result": "..."})
```

## 进一步阅读

- [SWAgent 项目文档](../README.md)
- [工具系统文档](../swagent/tools/README.md)
- [Agent 使用指南](../docs/user_guide.md)
