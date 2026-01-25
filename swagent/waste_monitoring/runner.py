"""
城市固废智能监测系统 - 主入口
"""
import asyncio
from pathlib import Path
from typing import Optional, Union
from dataclasses import dataclass

from swagent.stategraph import ExecutionConfig, ExecutionResult
from swagent.utils.logger import get_logger

from .state import RunMode, WasteMonitoringState, create_initial_state
from .workflow import create_waste_monitoring_workflow

logger = get_logger(__name__)


@dataclass
class MonitoringResult:
    """监测结果"""
    success: bool
    city_name: str
    mode: str
    total_tiles: int
    waste_count: int
    clean_count: int
    error_count: int
    detection_rate: float
    report_path: Optional[str]
    errors: list
    processing_log: list
    execution_result: Optional[ExecutionResult] = None


async def run_waste_monitoring(
    mode: Union[RunMode, str],
    input_path: str,
    city_name: str,
    output_dir: str = "./output",
    tile_size: int = 512,
    tile_overlap: int = 64,
    max_iterations: int = 10000,
    verbose: bool = True,
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
) -> MonitoringResult:
    """
    运行固废监测工作流

    Args:
        mode: 运行模式 (RunMode.TEST 或 RunMode.PRODUCTION)
        input_path: 输入路径
            - 测试模式: 大图路径
            - 生产模式: 小图目录路径
        city_name: 城市名称
        output_dir: 输出目录
        tile_size: 切割尺寸 (测试模式)
        tile_overlap: 重叠像素 (测试模式)
        max_iterations: 最大迭代次数
        verbose: 是否输出详细日志
        vl_base_url: 视觉模型API地址
        vl_api_key: 视觉模型API密钥
        vl_model: 视觉模型名称 (如 wuyu-vl-8b)
        llm_base_url: 文本模型API地址
        llm_api_key: 文本模型API密钥
        llm_model: 文本模型名称 (如 wuyu-30b)
        small_model_api_url: 小模型API地址
        small_model_api_key: 小模型API密钥
        small_model_name: 小模型名称

    Returns:
        MonitoringResult 对象
    """
    # 处理模式参数
    if isinstance(mode, str):
        mode = RunMode(mode)

    logger.info(f"启动固废监测工作流")
    logger.info(f"  模式: {mode.value}")
    logger.info(f"  城市: {city_name}")
    logger.info(f"  输入: {input_path}")
    logger.info(f"  输出: {output_dir}")
    if vl_model:
        logger.info(f"  视觉模型: {vl_model}")
    if llm_model:
        logger.info(f"  文本模型: {llm_model}")

    # 验证输入路径
    input_path_obj = Path(input_path)
    if mode == RunMode.TEST:
        if not input_path_obj.is_file():
            raise FileNotFoundError(f"测试模式需要大图文件，但未找到: {input_path}")
    else:
        if not input_path_obj.is_dir():
            raise NotADirectoryError(f"生产模式需要小图目录，但未找到: {input_path}")

    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 创建初始状态
    initial_state = create_initial_state(
        mode=mode,
        input_path=input_path,
        city_name=city_name,
        output_dir=output_dir,
        tile_size=tile_size,
        tile_overlap=tile_overlap,
        # 视觉模型配置
        vl_base_url=vl_base_url,
        vl_api_key=vl_api_key,
        vl_model=vl_model,
        # 文本模型配置
        llm_base_url=llm_base_url,
        llm_api_key=llm_api_key,
        llm_model=llm_model,
        # 小模型配置
        small_model_api_url=small_model_api_url,
        small_model_api_key=small_model_api_key,
        small_model_name=small_model_name
    )

    # 创建工作流
    graph = create_waste_monitoring_workflow()

    # 验证图
    validation_errors = graph.validate()
    if validation_errors:
        logger.error(f"工作流验证失败: {validation_errors}")
        raise ValueError(f"工作流验证失败: {validation_errors}")

    # 编译工作流
    config = ExecutionConfig(
        max_iterations=max_iterations
    )
    app = graph.compile(config=config)

    # 执行工作流
    try:
        result = await app.invoke(initial_state)

        final_state = result.state
        stats = final_state.get("statistics", {})

        return MonitoringResult(
            success=True,
            city_name=city_name,
            mode=mode.value,
            total_tiles=stats.get("total_tiles", 0),
            waste_count=stats.get("waste_count", 0),
            clean_count=stats.get("clean_count", 0),
            error_count=stats.get("error_count", 0),
            detection_rate=stats.get("detection_rate", 0),
            report_path=final_state.get("report_path"),
            errors=final_state.get("errors", []),
            processing_log=final_state.get("processing_log", []),
            execution_result=result
        )

    except Exception as e:
        logger.error(f"工作流执行失败: {e}")
        return MonitoringResult(
            success=False,
            city_name=city_name,
            mode=mode.value,
            total_tiles=0,
            waste_count=0,
            clean_count=0,
            error_count=0,
            detection_rate=0,
            report_path=None,
            errors=[str(e)],
            processing_log=[f"工作流执行失败: {e}"]
        )


async def run_test_mode(
    image_path: str,
    city_name: str,
    output_dir: str = "./output",
    tile_size: int = 512,
    tile_overlap: int = 64
) -> MonitoringResult:
    """
    测试模式快捷入口

    Args:
        image_path: 大图路径
        city_name: 城市名称
        output_dir: 输出目录
        tile_size: 切割尺寸
        tile_overlap: 重叠像素

    Returns:
        MonitoringResult
    """
    return await run_waste_monitoring(
        mode=RunMode.TEST,
        input_path=image_path,
        city_name=city_name,
        output_dir=output_dir,
        tile_size=tile_size,
        tile_overlap=tile_overlap
    )


async def run_production_mode(
    tiles_dir: str,
    city_name: str,
    output_dir: str = "./output"
) -> MonitoringResult:
    """
    生产模式快捷入口

    Args:
        tiles_dir: 小图目录
        city_name: 城市名称
        output_dir: 输出目录

    Returns:
        MonitoringResult
    """
    return await run_waste_monitoring(
        mode=RunMode.PRODUCTION,
        input_path=tiles_dir,
        city_name=city_name,
        output_dir=output_dir
    )


def run_sync(
    mode: Union[RunMode, str],
    input_path: str,
    city_name: str,
    **kwargs
) -> MonitoringResult:
    """
    同步执行入口

    Args:
        mode: 运行模式
        input_path: 输入路径
        city_name: 城市名称
        **kwargs: 其他参数

    Returns:
        MonitoringResult
    """
    return asyncio.run(run_waste_monitoring(
        mode=mode,
        input_path=input_path,
        city_name=city_name,
        **kwargs
    ))
