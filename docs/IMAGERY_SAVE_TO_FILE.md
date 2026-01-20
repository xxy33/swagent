# 影像切片工具 - 保存到本地示例

本文档演示如何使用 ImageryTool 将影像保存到本地文件夹。

## 功能说明

ImageryTool 现在支持三种返回格式：
1. **array** (默认): 返回数组形状和统计信息
2. **base64**: 返回 base64 编码的图片
3. **file**: 保存影像到本地文件 ✨ **新功能**

## 基础用法

### 1. 指定文件名保存

```python
import asyncio
from swagent.tools.domain import ImageryTool

async def save_with_custom_name():
    imagery = ImageryTool()

    result = await imagery.safe_execute(
        location=[116.4074, 39.9042],  # 北京
        source="google",
        zoom_level=18,
        point_size=1000,
        return_format="file",  # 保存到文件
        output_path="./imagery_output",  # 输出目录
        filename="beijing_satellite.png"  # 自定义文件名
    )

    if result.success:
        print(f"✅ 影像已保存到: {result.data['saved_path']}")
        print(f"   文件名: {result.data['filename']}")

asyncio.run(save_with_custom_name())
```

### 2. 自动生成文件名

如果不指定 `filename`，系统会自动生成包含坐标和时间戳的文件名：

```python
async def save_with_auto_name():
    imagery = ImageryTool()

    result = await imagery.safe_execute(
        location=[116.4074, 39.9042],
        source="google",
        zoom_level=18,
        point_size=1000,
        return_format="file",
        output_path="./imagery_output"  # 仅指定目录
        # filename 未指定，将自动生成
    )

    if result.success:
        print(f"自动生成的文件名: {result.data['filename']}")
        # 示例输出: google_116.4074_39.9042_20260120_143015.png
```

## 不同数据源示例

### Google Earth

```python
result = await imagery.safe_execute(
    location=[116.4074, 39.9042],
    source="google",
    zoom_level=19,  # 19 级分辨率约 0.3米
    point_size=2000,
    return_format="file",
    output_path="./satellite_images",
    filename="google_earth_highres.png"
)
```

### 吉林一号

```python
result = await imagery.safe_execute(
    location=[116.35, 39.85, 116.45, 39.95],  # 区域模式
    source="jilin",
    zoom_level=18,
    year=2024,  # 指定年份
    return_format="file",
    output_path="./satellite_images",
    filename="jilin1_beijing_2024.png"
)
```

### Sentinel-2

```python
result = await imagery.safe_execute(
    location=[116.397, 39.908],
    source="sentinel",
    date_range=["2024-05-01", "2024-09-01"],
    bands=["B4", "B3", "B2"],  # RGB 波段
    max_cloud_cover=10,  # 云量小于 10%
    return_format="file",
    output_path="./satellite_images",
    filename="sentinel2_summer_2024.png"
)
```

## 完整示例

```python
import asyncio
from swagent.tools.domain import ImageryTool

async def download_multiple_sources():
    """下载不同数据源的影像到本地"""
    imagery = ImageryTool()

    # 北京天安门坐标
    location = [116.397, 39.908]

    sources = [
        {
            "name": "Google Earth",
            "params": {
                "source": "google",
                "zoom_level": 18,
                "point_size": 1000
            }
        },
        {
            "name": "吉林一号 2024",
            "params": {
                "source": "jilin",
                "zoom_level": 18,
                "year": 2024,
                "point_size": 1000
            }
        }
    ]

    print("开始下载影像...")
    for src in sources:
        print(f"\n下载 {src['name']}...")
        result = await imagery.safe_execute(
            location=location,
            return_format="file",
            output_path="./my_satellite_images",
            **src['params']
        )

        if result.success:
            print(f"  ✅ 成功: {result.data['saved_path']}")
        else:
            print(f"  ❌ 失败: {result.error}")

asyncio.run(download_multiple_sources())
```

## 参数说明

### return_format="file" 时的参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| output_path | string | 否 | "./imagery_output" | 保存目录路径（支持相对路径和绝对路径） |
| filename | string | 否 | 自动生成 | 文件名（支持 .png, .jpg, .tiff 格式） |

### 自动生成的文件名格式

```
{source}_{longitude}_{latitude}_{timestamp}.png
```

示例：
- `google_116.4074_39.9042_20260120_143015.png`
- `jilin_2024_116.3500_39.8500_20260120_143020.png`
- `sentinel_116.3970_39.9080_20260120_143025.png`

## 返回数据

当 `return_format="file"` 时，返回数据包含：

```python
{
    "source": "google",
    "location": [116.4074, 39.9042],
    "shape": [1000, 1000, 3],
    "mode": "point",
    "zoom_level": 18,
    "saved_path": "/root/swagent/imagery_output/google_116.4074_39.9042_20260120_143015.png",
    "filename": "google_116.4074_39.9042_20260120_143015.png"
}
```

## 文件格式支持

支持的图像格式：
- **PNG** (推荐，无损压缩)
- **JPG/JPEG** (有损压缩，文件更小)
- **TIFF** (高质量，支持地理信息)

示例：
```python
filename="satellite.jpg"   # JPEG 格式
filename="satellite.tiff"  # TIFF 格式
filename="satellite.png"   # PNG 格式（默认）
```

## 注意事项

1. **目录自动创建**: 如果 `output_path` 目录不存在，会自动创建
2. **文件覆盖**: 如果文件已存在，会被覆盖
3. **路径类型**: 支持相对路径（如 `./images`）和绝对路径（如 `/home/user/images`）
4. **权限检查**: 确保有写入目标目录的权限
5. **磁盘空间**: 大尺寸影像会占用较多磁盘空间，建议定期清理

## 故障排除

### 问题 1: 权限错误
```
PermissionError: [Errno 13] Permission denied
```

**解决方案**: 检查目标目录的写入权限，或使用其他目录

### 问题 2: 磁盘空间不足
```
OSError: [Errno 28] No space left on device
```

**解决方案**: 清理磁盘空间或使用其他存储位置

### 问题 3: 文件名包含非法字符
```
OSError: [Errno 22] Invalid argument
```

**解决方案**: 文件名不要包含特殊字符（如 `/ \ : * ? " < > |`）

## 运行示例

```bash
# 运行完整的 GIS 示例（包含保存文件功能）
python examples/gis_agent_demo.py
```

示例将会在当前目录创建 `imagery_output` 文件夹并保存影像文件。
