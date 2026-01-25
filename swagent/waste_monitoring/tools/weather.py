"""
天气API封装
用于获取城市天气信息
"""
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from swagent.utils.logger import get_logger

logger = get_logger(__name__)


class WeatherAPI:
    """天气API封装"""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        初始化天气客户端

        Args:
            api_url: API地址
            api_key: API密钥
        """
        self.api_url = api_url or self._get_default_url()
        self.api_key = api_key or self._get_default_key()

    def _get_default_url(self) -> str:
        """获取默认API地址"""
        from swagent.utils.config import get_config
        try:
            config = get_config()
            return config.get("waste_monitoring.weather.api_url", "https://api.weatherapi.com/v1")
        except Exception:
            return "https://api.weatherapi.com/v1"

    def _get_default_key(self) -> Optional[str]:
        """获取默认API密钥"""
        from swagent.utils.config import get_config
        try:
            config = get_config()
            return config.get("waste_monitoring.weather.api_key")
        except Exception:
            return None

    async def get_current(self, city: str) -> Dict[str, Any]:
        """
        获取当前天气

        Args:
            city: 城市名称

        Returns:
            天气数据字典
        """
        logger.info(f"获取天气数据: {city}")

        try:
            if not self.api_key:
                logger.warning("天气API密钥未配置，使用模拟数据")
                return await self._mock_weather(city)

            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/current.json"
                params = {
                    "key": self.api_key,
                    "q": city,
                    "aqi": "yes"  # 获取空气质量数据
                }

                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        logger.warning(f"天气API错误: {response.status}")
                        return await self._mock_weather(city)

                    result = await response.json()
                    return self._parse_weather(result)

        except Exception as e:
            logger.warning(f"获取天气失败，使用模拟数据: {e}")
            return await self._mock_weather(city)

    async def get_forecast(self, city: str, days: int = 7) -> Dict[str, Any]:
        """
        获取天气预报

        Args:
            city: 城市名称
            days: 预报天数

        Returns:
            天气预报数据
        """
        try:
            if not self.api_key:
                return await self._mock_forecast(city, days)

            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/forecast.json"
                params = {
                    "key": self.api_key,
                    "q": city,
                    "days": days,
                    "aqi": "yes"
                }

                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        return await self._mock_forecast(city, days)

                    result = await response.json()
                    return self._parse_forecast(result)

        except Exception as e:
            logger.warning(f"获取天气预报失败: {e}")
            return await self._mock_forecast(city, days)

    async def _mock_weather(self, city: str) -> Dict[str, Any]:
        """模拟天气数据"""
        import random

        return {
            "city": city,
            "country": "中国",
            "timestamp": datetime.now().isoformat(),
            "current": {
                "temp_c": random.uniform(5, 30),
                "humidity": random.randint(30, 80),
                "condition": random.choice(["晴", "多云", "阴", "小雨"]),
                "wind_kph": random.uniform(5, 30),
                "wind_dir": random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
                "precip_mm": random.uniform(0, 10),
                "uv": random.uniform(1, 10)
            },
            "air_quality": {
                "aqi": random.randint(20, 150),
                "pm2_5": random.uniform(10, 100),
                "pm10": random.uniform(20, 150),
                "level": random.choice(["优", "良", "轻度污染", "中度污染"])
            },
            "is_mock": True
        }

    async def _mock_forecast(self, city: str, days: int) -> Dict[str, Any]:
        """模拟天气预报"""
        import random

        forecast_days = []
        base_date = datetime.now()

        for i in range(days):
            date = base_date + timedelta(days=i)
            forecast_days.append({
                "date": date.strftime("%Y-%m-%d"),
                "temp_max_c": random.uniform(15, 35),
                "temp_min_c": random.uniform(5, 20),
                "condition": random.choice(["晴", "多云", "阴", "小雨", "中雨"]),
                "chance_of_rain": random.randint(0, 100),
                "humidity": random.randint(40, 80)
            })

        return {
            "city": city,
            "forecast": forecast_days,
            "is_mock": True
        }

    def _parse_weather(self, result: Dict) -> Dict[str, Any]:
        """解析天气API响应"""
        location = result.get("location", {})
        current = result.get("current", {})
        aqi = current.get("air_quality", {})

        return {
            "city": location.get("name"),
            "country": location.get("country"),
            "timestamp": current.get("last_updated"),
            "current": {
                "temp_c": current.get("temp_c"),
                "humidity": current.get("humidity"),
                "condition": current.get("condition", {}).get("text"),
                "wind_kph": current.get("wind_kph"),
                "wind_dir": current.get("wind_dir"),
                "precip_mm": current.get("precip_mm"),
                "uv": current.get("uv")
            },
            "air_quality": {
                "aqi": aqi.get("us-epa-index"),
                "pm2_5": aqi.get("pm2_5"),
                "pm10": aqi.get("pm10"),
                "level": self._get_aqi_level(aqi.get("us-epa-index", 1))
            }
        }

    def _parse_forecast(self, result: Dict) -> Dict[str, Any]:
        """解析预报API响应"""
        location = result.get("location", {})
        forecast = result.get("forecast", {}).get("forecastday", [])

        forecast_days = []
        for day in forecast:
            day_data = day.get("day", {})
            forecast_days.append({
                "date": day.get("date"),
                "temp_max_c": day_data.get("maxtemp_c"),
                "temp_min_c": day_data.get("mintemp_c"),
                "condition": day_data.get("condition", {}).get("text"),
                "chance_of_rain": day_data.get("daily_chance_of_rain"),
                "humidity": day_data.get("avghumidity")
            })

        return {
            "city": location.get("name"),
            "forecast": forecast_days
        }

    def _get_aqi_level(self, aqi: int) -> str:
        """获取空气质量等级"""
        if aqi <= 50:
            return "优"
        elif aqi <= 100:
            return "良"
        elif aqi <= 150:
            return "轻度污染"
        elif aqi <= 200:
            return "中度污染"
        elif aqi <= 300:
            return "重度污染"
        else:
            return "严重污染"


async def fetch_weather(
    city: str,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    include_forecast: bool = False
) -> Dict[str, Any]:
    """
    便捷函数：获取城市天气

    Args:
        city: 城市名称
        api_url: API地址 (可选)
        api_key: API密钥 (可选)
        include_forecast: 是否包含预报

    Returns:
        天气数据字典
    """
    client = WeatherAPI(api_url=api_url, api_key=api_key)
    weather = await client.get_current(city)

    if include_forecast:
        forecast = await client.get_forecast(city)
        weather["forecast"] = forecast.get("forecast", [])

    return weather
