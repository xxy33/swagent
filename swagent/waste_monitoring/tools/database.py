"""
数据库操作封装
用于存储和查询历史监测数据
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from swagent.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MonitoringRecord:
    """监测记录"""
    id: str
    city_name: str
    monitoring_date: str
    total_tiles: int
    confirmed_count: int
    suspected_count: int
    clean_count: int
    detection_rate: float
    created_at: str
    report_path: Optional[str] = None
    data_path: Optional[str] = None


class DatabaseClient:
    """数据库客户端 (本地JSON文件存储)"""

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库客户端

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path or self._get_default_path()
        self._ensure_db_exists()

    def _get_default_path(self) -> str:
        """获取默认数据库路径"""
        from swagent.utils.config import get_config
        try:
            config = get_config()
            return config.get("waste_monitoring.database.path", "./data/waste_monitoring.json")
        except Exception:
            return "./data/waste_monitoring.json"

    def _ensure_db_exists(self):
        """确保数据库文件存在"""
        path = Path(self.db_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if not path.exists():
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"records": [], "sites": []}, f, ensure_ascii=False, indent=2)

    def _load_db(self) -> Dict:
        """加载数据库"""
        with open(self.db_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_db(self, data: Dict):
        """保存数据库"""
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def save_monitoring_results(
        self,
        city_name: str,
        results: List[Dict],
        statistics: Dict,
        report_path: Optional[str] = None
    ) -> str:
        """
        保存监测结果

        Args:
            city_name: 城市名称
            results: 所有检测结果
            statistics: 统计信息
            report_path: 报告路径

        Returns:
            记录ID
        """
        logger.info(f"保存监测结果: {city_name}")

        db = self._load_db()

        # 生成记录ID
        record_id = f"{city_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 保存详细结果到单独文件
        data_dir = Path(self.db_path).parent / "monitoring_data"
        data_dir.mkdir(exist_ok=True)
        data_path = str(data_dir / f"{record_id}.json")

        with open(data_path, "w", encoding="utf-8") as f:
            json.dump({
                "record_id": record_id,
                "city_name": city_name,
                "results": results,
                "created_at": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)

        # 创建监测记录
        record = MonitoringRecord(
            id=record_id,
            city_name=city_name,
            monitoring_date=datetime.now().strftime("%Y-%m-%d"),
            total_tiles=statistics.get("total_tiles", 0),
            confirmed_count=statistics.get("confirmed_count", 0),
            suspected_count=statistics.get("suspected_count", 0),
            clean_count=statistics.get("clean_count", 0),
            detection_rate=statistics.get("detection_rate", 0),
            created_at=datetime.now().isoformat(),
            report_path=report_path,
            data_path=data_path
        )

        db["records"].append(asdict(record))

        # 保存确认和疑似站点
        for result in results:
            if result.get("classification") in ["confirmed", "suspected"]:
                site = {
                    "record_id": record_id,
                    "tile_id": result.get("tile_id"),
                    "tile_path": result.get("tile_path"),
                    "classification": result.get("classification"),
                    "llm_description": result.get("llm_description"),
                    "llm_waste_type": result.get("llm_waste_type"),
                    "created_at": datetime.now().isoformat()
                }
                db["sites"].append(site)

        self._save_db(db)
        logger.info(f"监测结果已保存: {record_id}")

        return record_id

    async def query_historical(
        self,
        city_name: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        查询历史数据

        Args:
            city_name: 城市名称
            days: 查询天数

        Returns:
            历史数据汇总
        """
        logger.info(f"查询历史数据: {city_name}, 最近 {days} 天")

        db = self._load_db()
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        # 筛选记录
        records = [
            r for r in db.get("records", [])
            if r.get("city_name") == city_name and r.get("created_at", "") >= cutoff_date
        ]

        if not records:
            logger.info("未找到历史记录")
            return await self._mock_historical(city_name)

        # 计算统计
        total_confirmed = sum(r.get("confirmed_count", 0) for r in records)
        total_suspected = sum(r.get("suspected_count", 0) for r in records)
        total_tiles = sum(r.get("total_tiles", 0) for r in records)
        avg_detection_rate = sum(r.get("detection_rate", 0) for r in records) / len(records)

        # 趋势分析
        sorted_records = sorted(records, key=lambda x: x.get("monitoring_date", ""))
        trend = "stable"
        if len(sorted_records) >= 2:
            first_rate = sorted_records[0].get("detection_rate", 0)
            last_rate = sorted_records[-1].get("detection_rate", 0)
            if last_rate > first_rate * 1.2:
                trend = "increasing"
            elif last_rate < first_rate * 0.8:
                trend = "decreasing"

        return {
            "city_name": city_name,
            "period_days": days,
            "monitoring_count": len(records),
            "total_tiles_analyzed": total_tiles,
            "total_confirmed_sites": total_confirmed,
            "total_suspected_sites": total_suspected,
            "average_detection_rate": avg_detection_rate,
            "trend": trend,
            "records": records
        }

    async def _mock_historical(self, city_name: str) -> Dict[str, Any]:
        """模拟历史数据"""
        import random

        return {
            "city_name": city_name,
            "period_days": 30,
            "monitoring_count": random.randint(5, 15),
            "total_tiles_analyzed": random.randint(5000, 20000),
            "total_confirmed_sites": random.randint(10, 50),
            "total_suspected_sites": random.randint(20, 100),
            "average_detection_rate": random.uniform(0.01, 0.05),
            "trend": random.choice(["stable", "increasing", "decreasing"]),
            "records": [],
            "is_mock": True
        }

    async def get_site_details(
        self,
        city_name: str,
        classification: Optional[str] = None
    ) -> List[Dict]:
        """
        获取站点详情

        Args:
            city_name: 城市名称
            classification: 分类筛选

        Returns:
            站点列表
        """
        db = self._load_db()

        sites = db.get("sites", [])

        # 需要通过record_id关联城市
        records = {r["id"]: r for r in db.get("records", [])}

        filtered_sites = []
        for site in sites:
            record = records.get(site.get("record_id", ""))
            if record and record.get("city_name") == city_name:
                if classification is None or site.get("classification") == classification:
                    filtered_sites.append(site)

        return filtered_sites


async def query_historical_data(
    city_name: str,
    days: int = 30,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    便捷函数：查询历史数据

    Args:
        city_name: 城市名称
        days: 查询天数
        db_path: 数据库路径 (可选)

    Returns:
        历史数据汇总
    """
    client = DatabaseClient(db_path)
    return await client.query_historical(city_name, days)


async def save_results_to_db(
    city_name: str,
    results: List[Dict],
    statistics: Dict,
    report_path: Optional[str] = None,
    db_path: Optional[str] = None
) -> str:
    """
    便捷函数：保存结果到数据库

    Args:
        city_name: 城市名称
        results: 检测结果
        statistics: 统计信息
        report_path: 报告路径
        db_path: 数据库路径 (可选)

    Returns:
        记录ID
    """
    client = DatabaseClient(db_path)
    return await client.save_monitoring_results(city_name, results, statistics, report_path)
