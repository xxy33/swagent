# 影像切片工具更新 - 保存到本地文件功能

## 更新概述

已成功为 `ImageryTool` 添加了将影像保存到本地文件夹的功能！

## 新增功能 ✨

### 1. 文件保存模式
- 新增 `return_format="file"` 选项
- 支持保存为 PNG、JPG、TIFF 格式
- 自动创建输出目录

### 2. 灵活的文件命名
- **自定义文件名**: 通过 `filename` 参数指定
- **自动生成**: 包含数据源、坐标、时间戳的文件名

### 3. 路径配置
- **output_path**: 指定保存目录（支持相对/绝对路径）
- 默认保存到 `./imagery_output`

## 代码变更

### 1. 工具参数更新 (`imagery_tool.py`)

**新增参数**:
```python
ToolParameter(
    name="return_format",
    enum=["array", "base64", "file"]  # 新增 "file"
)

ToolParameter(
    name="output_path",
    default="./imagery_output"
)

ToolParameter(
    name="filename",
    description="文件名（可选），不指定则自动生成"
)
```

### 2. 新增方法

**`_save_to_file()` 方法**:
- 创建输出目录
- 生成自动文件名（如果需要）
- 保存 numpy 数组为图像文件
- 返回绝对路径

```python
def _save_to_file(
    self,
    img_array: np.ndarray,
    output_path: str,
    filename: Optional[str] = None,
    source: str = "imagery",
    location: List[float] = None
) -> str:
    """将 numpy 数组保存到本地文件"""
```

### 3. 更新查询方法

所有三个数据源的查询方法都已更新以支持文件保存：
- `_query_google()` ✅
- `_query_jilin()` ✅
- `_query_sentinel()` ✅

## 使用示例

### 基础用法

```python
from swagent.tools.domain import ImageryTool

imagery = ImageryTool()

# 保存到文件
result = await imagery.safe_execute(
    location=[116.4074, 39.9042],
    source="google",
    zoom_level=18,
    point_size=1000,
    return_format="file",  # 关键参数
    output_path="./my_images",
    filename="beijing.png"
)

print(f"已保存到: {result.data['saved_path']}")
```

### 自动文件名

```python
# 不指定 filename，自动生成
result = await imagery.safe_execute(
    location=[116.4074, 39.9042],
    source="google",
    zoom_level=18,
    return_format="file",
    output_path="./satellite_images"
)

# 自动生成的文件名示例:
# google_116.4074_39.9042_20260120_143530.png
```

### 返回数据

```python
{
    "source": "google",
    "location": [116.4074, 39.9042],
    "shape": [1000, 1000, 3],
    "mode": "point",
    "zoom_level": 18,
    "saved_path": "/root/swagent/my_images/beijing.png",  # 新增
    "filename": "beijing.png"  # 新增
}
```

## 新增文件

### 1. 文档
- **`docs/IMAGERY_SAVE_TO_FILE.md`**: 详细的功能说明和示例

### 2. 示例代码
- **`examples/imagery_download_demo.py`**: 完整的下载示例
  - 下载单个位置
  - 批量下载多个城市
  - 不同格式保存
  - 自动文件名生成

### 3. 更新的文件
- `swagent/tools/domain/imagery_tool.py`: 核心实现
- `examples/gis_agent_demo.py`: 更新示例
- `docs/GIS_TOOLS.md`: 更新文档

## 测试

文件保存功能已通过测试：

```bash
# 运行影像下载示例
python examples/imagery_download_demo.py
```

## 特性亮点

✅ **自动目录创建**: 目录不存在时自动创建
✅ **智能文件名**: 自动生成包含位置和时间的文件名
✅ **多格式支持**: PNG, JPG, TIFF
✅ **路径灵活**: 支持相对路径和绝对路径
✅ **三种数据源**: Google Earth, 吉林一号, Sentinel-2
✅ **完整文档**: 详细的使用说明和示例

## 示例输出

运行示例后，会在指定目录创建影像文件：

```
satellite_images/
├── beijing_satellite.png
├── shanghai_satellite.png
├── guangzhou_satellite.png
└── cities/
    ├── 北京_satellite.png
    ├── 上海_satellite.png
    └── 深圳_satellite.png
```

## 注意事项

1. **依赖要求**: 需要 `Pillow` 和 `numpy`
2. **权限检查**: 确保对输出目录有写入权限
3. **磁盘空间**: 大尺寸影像会占用较多空间
4. **文件覆盖**: 同名文件会被覆盖

## 向后兼容

完全向后兼容！原有的 `return_format="array"` 和 `return_format="base64"` 模式保持不变。

## 总结

影像切片工具现在支持三种输出模式：
1. **array** (默认): 返回数组信息
2. **base64**: 返回编码图片
3. **file** (新增): 保存到本地文件 ✨

所有功能已实现并测试通过！
