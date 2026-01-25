"""
城市固废智能监测系统 - StateGraph 工作流定义
"""
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from swagent.stategraph import (
    StateGraph,
    ExecutionConfig,
    START,
    END,
)
from swagent.utils.logger import get_logger

from .state import WasteMonitoringState, TileResult, RunMode

logger = get_logger(__name__)


def create_waste_monitoring_workflow() -> StateGraph:
    """
    创建固废监测工作流

    Returns:
        配置好的StateGraph实例
    """

    graph = StateGraph(WasteMonitoringState)

    # ===== 节点1: 初始化工作流 =====
    @graph.node()
    async def init_workflow(state: WasteMonitoringState) -> dict:
        """初始化工作流"""
        logger.info(f"初始化固废监测工作流 - 模式: {state['mode']}, 城市: {state['city_name']}")

        return {
            "start_time": datetime.now().isoformat(),
            "processing_log": [f"[{datetime.now().strftime('%H:%M:%S')}] 工作流初始化完成"],
            "results": [],
            "waste_sites": [],
            "clean_count": 0,
            "error_count": 0,
            "current_index": 0,
            "errors": [],
            "report_sections": {},
            "statistics": {}
        }

    # ===== 节点2a: 测试模式 - 加载并切割大图 =====
    @graph.node()
    async def load_and_split_image(state: WasteMonitoringState) -> dict:
        """[测试模式] 加载大图并切割"""
        from .processors.image_tiler import split_image

        logger.info(f"开始切割大图: {state['input_path']}")

        tile_paths = await split_image(
            state["input_path"],
            tile_size=state.get("tile_size", 512),
            overlap=state.get("tile_overlap", 64),
            output_dir=str(Path(state["output_dir"]) / "tiles")
        )

        log_msg = f"[{datetime.now().strftime('%H:%M:%S')}] 大图切割完成，共 {len(tile_paths)} 个图块"
        logger.info(log_msg)

        return {
            "tile_paths": tile_paths,
            "total_tiles": len(tile_paths),
            "processing_log": state["processing_log"] + [log_msg]
        }

    # ===== 节点2b: 生产模式 - 加载小图列表 =====
    @graph.node()
    async def load_tile_list(state: WasteMonitoringState) -> dict:
        """[生产模式] 加载已切割的小图列表"""
        tile_dir = Path(state["input_path"])

        # 支持多种图片格式
        tile_paths = []
        for ext in ["*.png", "*.jpg", "*.jpeg", "*.tif", "*.tiff"]:
            tile_paths.extend(sorted(tile_dir.glob(ext)))

        tile_paths = [str(p) for p in tile_paths]

        log_msg = f"[{datetime.now().strftime('%H:%M:%S')}] 加载小图列表完成，共 {len(tile_paths)} 张"
        logger.info(log_msg)

        return {
            "tile_paths": tile_paths,
            "total_tiles": len(tile_paths),
            "processing_log": state["processing_log"] + [log_msg]
        }

    # ===== 节点3: 处理单张图片 (核心节点) =====
    @graph.node()
    async def process_single_tile(state: WasteMonitoringState) -> dict:
        """处理单张图片"""
        from .processors.llm_detector import call_llm_api
        from .processors.small_model_detector import call_small_model_api

        idx = state["current_index"]
        tile_path = state["tile_paths"][idx]
        tile_id = Path(tile_path).stem

        log = state["processing_log"].copy()
        log.append(f"[{datetime.now().strftime('%H:%M:%S')}] [{idx+1}/{state['total_tiles']}] 处理: {tile_id}")

        errors = state["errors"].copy()

        try:
            # Step 1: 调用视觉模型 API (wuyu-vl-8b)
            logger.debug(f"调用视觉模型检测: {tile_id}")
            llm_result = await call_llm_api(
                tile_path,
                base_url=state.get("vl_base_url"),
                api_key=state.get("vl_api_key"),
                model=state.get("vl_model")
            )

            label = llm_result.get("label", 0)
            is_error = llm_result.get("error", False)

            # 构建结果
            result: TileResult = {
                "tile_id": tile_id,
                "tile_path": tile_path,
                "label": label,
                "reasoning": llm_result.get("reasoning", ""),
                "description": llm_result.get("description", ""),
                "boundingbox": llm_result.get("boundingbox", []),
                "processed_image_path": None,
                "classification": "error" if is_error else ("waste" if label == 1 else "clean"),
                "error": is_error
            }

            # Step 2: 如果检测到垃圾 (label=1)，调用小模型处理图像
            if label == 1 and not is_error:
                logger.debug(f"检测到垃圾，调用小模型处理图像: {tile_id}")
                try:
                    small_result = await call_small_model_api(
                        image_path=tile_path,
                        boundingboxes=llm_result.get("boundingbox", []),
                        output_dir=state.get("output_dir", "./output"),
                        base_url=state.get("small_model_api_url"),
                        api_key=state.get("small_model_api_key"),
                        model=state.get("small_model_name")
                    )
                    if small_result.get("success"):
                        result["processed_image_path"] = small_result.get("output_path")
                        log.append(f"  → 检测到垃圾，已保存处理后图像")
                except Exception as e:
                    logger.warning(f"小模型处理失败: {e}")
                    log.append(f"  → 检测到垃圾，但图像处理失败: {e}")

            # 添加日志
            if is_error:
                log.append(f"  → 检测失败: {llm_result.get('reasoning', '')[:50]}")
            elif label == 1:
                bbox_count = len(llm_result.get("boundingbox", []))
                log.append(f"  → 发现垃圾堆存 ({bbox_count} 个区域)")
            else:
                log.append(f"  → 清洁区域")

        except Exception as e:
            logger.error(f"处理图片失败: {tile_id}, 错误: {e}")
            errors.append(f"{tile_id}: {str(e)}")

            result: TileResult = {
                "tile_id": tile_id,
                "tile_path": tile_path,
                "label": -1,
                "reasoning": f"ERROR: {str(e)}",
                "description": "Processing failed",
                "boundingbox": [],
                "processed_image_path": None,
                "classification": "error",
                "error": True
            }
            log.append(f"  → 处理失败: {str(e)[:50]}")

        # 更新统计
        new_results = state["results"] + [result]
        new_waste_sites = state["waste_sites"].copy()
        new_clean_count = state["clean_count"]
        new_error_count = state["error_count"]

        if result["classification"] == "waste":
            new_waste_sites.append(result)
        elif result["classification"] == "clean":
            new_clean_count += 1
        else:
            new_error_count += 1

        return {
            "results": new_results,
            "waste_sites": new_waste_sites,
            "clean_count": new_clean_count,
            "error_count": new_error_count,
            "current_index": idx + 1,
            "processing_log": log,
            "errors": errors
        }

    # ===== 节点4: 检查进度 (条件路由函数) =====
    def check_progress(state: WasteMonitoringState) -> str:
        """检查是否继续处理"""
        if state["current_index"] < state["total_tiles"]:
            # 每处理10张输出一次进度
            if state["current_index"] % 10 == 0:
                logger.info(f"处理进度: {state['current_index']}/{state['total_tiles']}")
            return "continue"
        logger.info(f"所有图片处理完成: {state['total_tiles']} 张")
        return "done"

    # ===== 节点5: 汇总结果 =====
    @graph.node()
    async def aggregate_results(state: WasteMonitoringState) -> dict:
        """汇总所有结果"""
        total = state["total_tiles"]
        waste_count = len(state["waste_sites"])
        clean = state["clean_count"]
        error = state["error_count"]

        detection_rate = waste_count / total if total > 0 else 0

        statistics = {
            "total_tiles": total,
            "waste_count": waste_count,
            "clean_count": clean,
            "error_count": error,
            "detection_rate": round(detection_rate, 4),
            "waste_rate": round(waste_count / total, 4) if total > 0 else 0
        }

        log_msg = (
            f"[{datetime.now().strftime('%H:%M:%S')}] 结果汇总完成: "
            f"垃圾堆存{waste_count}处, 清洁{clean}处, 错误{error}处 "
            f"(检出率: {detection_rate:.2%})"
        )
        logger.info(log_msg)

        return {
            "statistics": statistics,
            "processing_log": state["processing_log"] + [log_msg]
        }

    # ===== 节点6: 获取外部数据 =====
    @graph.node()
    async def fetch_external_data(state: WasteMonitoringState) -> dict:
        """获取外部数据（天气、搜索、历史数据）"""
        from swagent.tools.domain.weather_tool import WeatherTool
        from swagent.tools.domain.location_tool import LocationTool

        logger.info("获取外部数据...")

        weather_data = None
        search_results = []
        historical_data = None

        # 1. 获取城市经纬度
        try:
            location_tool = LocationTool()
            location_result = await location_tool.execute(address=state["city_name"])
            if location_result.success:
                lat = location_result.data["latitude"]
                lon = location_result.data["longitude"]
                logger.info(f"城市经纬度: {state['city_name']} -> ({lat}, {lon})")

                # 2. 查询2024年9月1日的天气
                weather_tool = WeatherTool()
                weather_result = await weather_tool.execute(
                    latitude=lat,
                    longitude=lon,
                    when="2024-09-01T12:00",
                    timezone="Asia/Shanghai"
                )
                if weather_result.success:
                    weather_data = {
                        "city": state["city_name"],
                        "coordinates": {"latitude": lat, "longitude": lon},
                        "query_time": "2024-09-01T12:00",
                        "data": weather_result.data
                    }
                    logger.info(f"天气数据获取成功: {weather_data['data']}")
                else:
                    logger.warning(f"天气查询失败: {weather_result.error}")
            else:
                logger.warning(f"城市经纬度查询失败: {location_result.error}")
        except Exception as e:
            logger.warning(f"获取天气数据失败: {e}")

        # 3. 搜索和历史数据（可选）
        try:
            from .tools.meta_search import meta_search
            from .tools.database import query_historical_data
            search_results = await meta_search(f"{state['city_name']} 固废管理 政策 环保")
            historical_data = await query_historical_data(state["city_name"])
        except Exception as e:
            logger.warning(f"获取搜索/历史数据失败: {e}")

        log_msg = f"[{datetime.now().strftime('%H:%M:%S')}] 外部数据获取完成"
        logger.info(log_msg)

        return {
            "weather_data": weather_data,
            "search_results": search_results,
            "historical_data": historical_data,
            "processing_log": state["processing_log"] + [log_msg]
        }

    # ===== 节点7: 生成报告 =====
    @graph.node()
    async def generate_report(state: WasteMonitoringState) -> dict:
        """生成综合监管报告（使用文本模型 wuyu-30b）"""
        from .report.generator import generate_monitoring_report

        logger.info("生成监管报告...")

        try:
            # 传递文本模型配置用于报告生成
            report = await generate_monitoring_report(
                state,
                llm_base_url=state.get("llm_base_url"),
                llm_api_key=state.get("llm_api_key"),
                llm_model=state.get("llm_model")
            )
        except Exception as e:
            logger.error(f"报告生成失败: {e}")
            report = _generate_fallback_report(state)

        log_msg = f"[{datetime.now().strftime('%H:%M:%S')}] 报告生成完成"
        logger.info(log_msg)

        return {
            "final_report": report,
            "processing_log": state["processing_log"] + [log_msg]
        }

    # ===== 节点8: 保存输出 =====
    @graph.node()
    async def save_output(state: WasteMonitoringState) -> dict:
        """保存报告和数据"""
        from .tools.database import save_results_to_db

        output_dir = Path(state["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

        # 生成报告文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"waste_monitoring_report_{state['city_name']}_{timestamp}.md"
        report_path = str(output_dir / report_filename)

        # 保存报告
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(state["final_report"])

        logger.info(f"报告已保存: {report_path}")

        # 保存到数据库
        try:
            record_id = await save_results_to_db(
                city_name=state["city_name"],
                results=state["results"],
                statistics=state["statistics"],
                report_path=report_path
            )
            logger.info(f"数据已保存到数据库: {record_id}")
        except Exception as e:
            logger.warning(f"数据库保存失败: {e}")

        log_msg = f"[{datetime.now().strftime('%H:%M:%S')}] 报告已保存: {report_path}"

        return {
            "report_path": report_path,
            "end_time": datetime.now().isoformat(),
            "processing_log": state["processing_log"] + [log_msg, "工作流执行完成"]
        }

    # ===== 定义边 =====

    # 入口点
    graph.set_entry_point("init_workflow")

    # 根据模式选择路径
    graph.add_conditional_edge(
        "init_workflow",
        lambda s: "test" if s["mode"] == "test" else "prod",
        {
            "test": "load_and_split_image",
            "prod": "load_tile_list"
        }
    )

    # 加载后进入处理循环
    graph.add_edge("load_and_split_image", "process_single_tile")
    graph.add_edge("load_tile_list", "process_single_tile")

    # 处理循环
    graph.add_conditional_edge(
        "process_single_tile",
        check_progress,
        {
            "continue": "process_single_tile",  # 继续处理下一张
            "done": "aggregate_results"          # 处理完成
        }
    )

    # 后续流程
    graph.add_edge("aggregate_results", "fetch_external_data")
    graph.add_edge("fetch_external_data", "generate_report")
    graph.add_edge("generate_report", "save_output")

    # 出口点
    graph.set_exit_point("save_output")

    return graph


def _generate_fallback_report(state: WasteMonitoringState) -> str:
    """生成备用报告（当报告生成失败时使用）"""
    stats = state.get("statistics", {})

    report = f"""
# 城市固废综合监管报告

## 基本信息

- **城市**: {state.get('city_name', '未知')}
- **监测日期**: {state.get('monitoring_date', '未知')}
- **分析图块数**: {stats.get('total_tiles', 0)}

## 检测结果汇总

| 类别 | 数量 | 占比 |
|------|------|------|
| 垃圾堆存点 | {stats.get('waste_count', 0)} | {stats.get('waste_rate', 0):.2%} |
| 清洁区域 | {stats.get('clean_count', 0)} | - |
| 检测失败 | {stats.get('error_count', 0)} | - |

## 垃圾堆存点列表

"""
    for site in state.get("waste_sites", [])[:10]:
        report += f"- **{site.get('tile_id', '未知')}**: {site.get('description', '')[:100]}\n"

    if len(state.get("waste_sites", [])) > 10:
        report += f"\n... 共 {len(state['waste_sites'])} 处\n"

    report += f"""

---

*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*系统: 城市固废智能监测系统*
"""

    return report
