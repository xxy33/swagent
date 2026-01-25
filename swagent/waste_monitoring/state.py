"""
城市固废智能监测系统 - 状态定义
"""
from typing import TypedDict, List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


class RunMode(Enum):
    """运行模式"""
    TEST = "test"           # 测试模式：大图切割后处理
    PRODUCTION = "prod"     # 生产模式：直接处理小图


class Classification(Enum):
    """检测分类"""
    WASTE = "waste"         # 有垃圾 (label=1)
    CLEAN = "clean"         # 无垃圾 (label=0)
    ERROR = "error"         # 检测失败 (label=-1)


class TileResult(TypedDict):
    """单张图片处理结果"""
    tile_id: str                        # 图片ID
    tile_path: str                      # 图片路径

    # 大模型结果
    label: int                          # 1=有垃圾, 0=无垃圾, -1=错误
    reasoning: str                      # 推理过程
    description: str                    # 描述
    boundingbox: List[List[float]]      # [[ymin, xmin, ymax, xmax], ...]

    # 处理后图像路径 (仅 label=1 时有值)
    processed_image_path: Optional[str]

    # 最终分类
    classification: str                 # waste/clean/error

    # 错误信息 (仅 label=-1 时有值)
    error: Optional[bool]


class WasteMonitoringState(TypedDict):
    """固废监测工作流状态"""

    # ===== 输入参数 =====
    mode: str                           # 运行模式: test/prod
    city_name: str                      # 城市名称
    monitoring_date: str                # 监测日期
    input_path: str                     # 输入路径 (大图或小图目录)
    output_dir: str                     # 输出目录

    # ===== 图像处理 =====
    # 测试模式专用
    source_image_path: Optional[str]    # 原始大图路径
    tile_size: int                      # 切割尺寸
    tile_overlap: int                   # 重叠像素

    # 通用
    tile_paths: List[str]               # 待处理的小图路径列表
    total_tiles: int                    # 总图片数
    current_index: int                  # 当前处理索引

    # ===== 模型配置 =====
    # 视觉模型配置 (用于图像检测)
    vl_base_url: Optional[str]          # 视觉模型API地址
    vl_api_key: Optional[str]           # 视觉模型API密钥
    vl_model: Optional[str]             # 视觉模型名称

    # 文本模型配置 (用于报告生成)
    llm_base_url: Optional[str]         # 文本模型API地址
    llm_api_key: Optional[str]          # 文本模型API密钥
    llm_model: Optional[str]            # 文本模型名称

    # 小模型配置 (用于图像处理)
    small_model_api_url: Optional[str]  # 小模型API地址
    small_model_api_key: Optional[str]  # 小模型API密钥
    small_model_name: Optional[str]     # 小模型名称

    # ===== 处理结果 =====
    results: List[TileResult]           # 所有处理结果

    # 分类汇总
    waste_sites: List[TileResult]       # 检测到垃圾的图片
    clean_count: int                    # 清洁区域数量
    error_count: int                    # 检测失败数量

    # ===== 外部数据 =====
    weather_data: Optional[Dict]        # 天气数据
    search_results: Optional[List]      # 秘塔搜索结果
    historical_data: Optional[Dict]     # 历史数据

    # ===== 报告 =====
    report_sections: Dict[str, str]     # 报告章节
    final_report: Optional[str]         # 最终报告
    report_path: Optional[str]          # 报告保存路径

    # ===== 元数据 =====
    processing_log: List[str]           # 处理日志
    errors: List[str]                   # 错误记录
    start_time: str                     # 开始时间
    end_time: Optional[str]             # 结束时间
    statistics: Dict[str, Any]          # 统计信息


def create_initial_state(
    mode: RunMode,
    input_path: str,
    city_name: str,
    output_dir: str = "./output",
    tile_size: int = 512,
    tile_overlap: int = 64,
    # 视觉模型配置 (用于图像检测)
    vl_base_url: str = None,
    vl_api_key: str = None,
    vl_model: str = None,
    # 文本模型配置 (用于报告生成)
    llm_base_url: str = None,
    llm_api_key: str = None,
    llm_model: str = None,
    # 小模型配置 (用于图像处理)
    small_model_api_url: str = None,
    small_model_api_key: str = None,
    small_model_name: str = None
) -> WasteMonitoringState:
    """
    创建初始状态

    Args:
        mode: 运行模式
        input_path: 输入路径
        city_name: 城市名称
        output_dir: 输出目录
        tile_size: 切割尺寸 (测试模式)
        tile_overlap: 重叠像素 (测试模式)
        vl_base_url: 视觉模型API地址
        vl_api_key: 视觉模型API密钥
        vl_model: 视觉模型名称
        llm_base_url: 文本模型API地址
        llm_api_key: 文本模型API密钥
        llm_model: 文本模型名称
        small_model_api_url: 小模型API地址
        small_model_api_key: 小模型API密钥
        small_model_name: 小模型名称

    Returns:
        初始化的状态对象
    """
    return WasteMonitoringState(
        # 输入参数
        mode=mode.value,
        city_name=city_name,
        monitoring_date=datetime.now().strftime("%Y-%m-%d"),
        input_path=input_path,
        output_dir=output_dir,

        # 图像处理
        source_image_path=input_path if mode == RunMode.TEST else None,
        tile_size=tile_size,
        tile_overlap=tile_overlap,
        tile_paths=[],
        total_tiles=0,
        current_index=0,

        # 模型配置
        vl_base_url=vl_base_url,
        vl_api_key=vl_api_key,
        vl_model=vl_model,
        llm_base_url=llm_base_url,
        llm_api_key=llm_api_key,
        llm_model=llm_model,
        small_model_api_url=small_model_api_url,
        small_model_api_key=small_model_api_key,
        small_model_name=small_model_name,

        # 处理结果
        results=[],
        waste_sites=[],
        clean_count=0,
        error_count=0,

        # 外部数据
        weather_data=None,
        search_results=None,
        historical_data=None,

        # 报告
        report_sections={},
        final_report=None,
        report_path=None,

        # 元数据
        processing_log=[],
        errors=[],
        start_time="",
        end_time=None,
        statistics={}
    )
