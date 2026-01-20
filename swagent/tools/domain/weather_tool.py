"""
天气查询工具
根据 GIS 坐标和时间，调取天气 API 获取天气数据
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import List, Dict, Optional
import requests

from swagent.tools.base_tool import (
    BaseTool,
    ToolCategory,
    ToolParameter,
    ToolResult
)
from swagent.utils.logger import get_logger

logger = get_logger(__name__)


class WeatherTool(BaseTool):
    """
    天气查询工具

    根据 GIS 坐标和时间，调取 Open-Meteo API 获取天气数据
    支持当前天气查询和指定时间的历史/预报天气查询
    """

    def __init__(self):
        super().__init__()
        self.base_url = "https://api.open-meteo.com/v1/forecast"

    @property
    def name(self) -> str:
        return "weather_query"

    @property
    def description(self) -> str:
        return "根据 GIS 坐标（纬度、经度）和时间查询天气数据，包括温度、湿度、降水量和风速等信息"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.DOMAIN

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="latitude",
                type="number",
                description="纬度 (范围: -90 到 90)",
                required=True
            ),
            ToolParameter(
                name="longitude",
                type="number",
                description="经度 (范围: -180 到 180)",
                required=True
            ),
            ToolParameter(
                name="when",
                type="string",
                description="查询时间，ISO8601 格式 (如 '2026-01-20T14:00')。不指定则查询当前天气",
                required=False,
                default=None
            ),
            ToolParameter(
                name="timezone",
                type="string",
                description="时区 (如 'Asia/Shanghai', 'UTC')，默认为 'Asia/Shanghai'",
                required=False,
                default="Asia/Shanghai"
            )
        ]

    def get_return_description(self) -> str:
        return "返回包含天气数据的字典，包括模式（current/hourly）、时间、温度、湿度、降水量、风速等信息"

    def get_examples(self) -> List[Dict]:
        return [
            {
                "input": {
                    "latitude": 39.9042,
                    "longitude": 116.4074
                },
                "output": {
                    "mode": "current",
                    "data": {
                        "time": "2026-01-20T14:00",
                        "temperature_2m": 5.2,
                        "relative_humidity_2m": 45,
                        "precipitation": 0.0,
                        "wind_speed_10m": 3.5
                    }
                }
            },
            {
                "input": {
                    "latitude": 39.9042,
                    "longitude": 116.4074,
                    "when": "2026-01-20T14:00",
                    "timezone": "Asia/Shanghai"
                },
                "output": {
                    "mode": "hourly",
                    "data": {
                        "time": "2026-01-20T14:00",
                        "temperature_2m": 5.2,
                        "relative_humidity_2m": 45,
                        "precipitation": 0.0,
                        "wind_speed_10m": 3.5
                    }
                }
            }
        ]

    async def execute(self, **kwargs) -> ToolResult:
        """执行天气查询"""
        lat = kwargs["latitude"]
        lon = kwargs["longitude"]
        when = kwargs.get("when")
        tz = kwargs.get("timezone", "Asia/Shanghai")

        logger.info(f"天气查询 - 坐标: ({lat}, {lon}), 时间: {when or 'current'}, 时区: {tz}")

        try:
            result = self._get_weather(lat, lon, when, tz)

            logger.info(f"天气查询完成 - 模式: {result['mode']}")

            return ToolResult(
                success=True,
                data=result,
                metadata={
                    "source": "Open-Meteo API",
                    "coordinates": {"latitude": lat, "longitude": lon},
                    "timezone": tz
                }
            )

        except Exception as e:
            logger.error(f"天气查询异常: {str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                data=None,
                error=f"Weather query error: {str(e)}"
            )

    def _get_weather(
        self,
        lat: float,
        lon: float,
        when: Optional[str] = None,
        tz: str = "Asia/Shanghai"
    ) -> Dict:
        """
        核心天气查询逻辑

        参数:
            lat: 纬度
            lon: 经度
            when: 查询时间，ISO8601 格式字符串或 None
            tz: 时区

        返回:
            包含天气数据的字典
        """
        # 未指定时间：取 current
        if when is None:
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
                "timezone": tz
            }
            j = requests.get(self.base_url, params=params, timeout=10).json()
            return {"mode": "current", "data": j.get("current", {})}

        # 规范化 when
        when = when.replace(" ", "T")
        dt = datetime.fromisoformat(when)

        # 将时间转换到指定时区，并取整点
        tzinfo = ZoneInfo(tz)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tzinfo)
        else:
            dt = dt.astimezone(tzinfo)

        dt_hour = dt.replace(minute=0, second=0, microsecond=0)
        dt_next = dt_hour + timedelta(hours=1)

        # 构造本地时区的 start/end（不带偏移）
        start_iso = dt_hour.strftime("%Y-%m-%dT%H:%M")
        end_iso = dt_next.strftime("%Y-%m-%dT%H:%M")

        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
            "timezone": tz,
            "start": start_iso,
            "end": end_iso,
            "timeformat": "iso8601"
        }

        j = requests.get(self.base_url, params=params, timeout=10).json()
        hourly = j.get("hourly", {})
        times = hourly.get("time", [])

        # 按 start_iso 精确匹配
        idx = None
        for i, t in enumerate(times):
            if t.startswith(start_iso):
                idx = i
                break
        if idx is None and times:
            idx = 0

        if idx is None:
            return {"mode": "hourly", "data": {}, "msg": "no hourly data returned"}

        out = {"time": times[idx]}
        for k, v in hourly.items():
            if isinstance(v, list) and len(v) > idx:
                out[k] = v[idx]

        return {"mode": "hourly", "data": out}
