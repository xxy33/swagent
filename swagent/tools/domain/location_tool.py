"""
LocationTool - 地名转经纬度工具
使用高德地图 API 将地址/地名转换为经纬度坐标
"""
import os
import requests
from typing import Dict, Any, Optional, List

from swagent.tools.base_tool import BaseTool, ToolResult, ToolCategory, ToolParameter
from swagent.utils.logger import get_logger

logger = get_logger(__name__)


class LocationTool(BaseTool):
    """地名转经纬度工具"""

    def __init__(self):
        super().__init__()
        # 从环境变量读取高德地图 API Key
        self.amap_key = os.getenv("AMAP_KEY", "51e748084f28af808466fd0c42a37302")
        self.base_url = "https://restapi.amap.com/v3/geocode/geo"

    @property
    def name(self) -> str:
        return "location_geocoding"

    @property
    def description(self) -> str:
        return "将地址或地名转换为经纬度坐标。支持城市名、地标、详细地址等。返回经度(longitude)和纬度(latitude)。"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.DOMAIN

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="address",
                type="string",
                description="要查询的地址或地名，如'北京'、'上海东方明珠'、'深圳市南山区'等",
                required=True
            ),
            ToolParameter(
                name="city",
                type="string",
                description="可选，指定查询的城市范围，可以提高查询准确性",
                required=False
            )
        ]

    def get_return_description(self) -> str:
        return "返回包含地理编码结果的字典，包括经度(longitude)、纬度(latitude)、完整地址(formatted_address)、省份、城市、区县等信息"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "要查询的地址或地名，如'北京'、'上海东方明珠'、'深圳市南山区'等"
                },
                "city": {
                    "type": "string",
                    "description": "可选，指定查询的城市范围，可以提高查询准确性"
                }
            },
            "required": ["address"]
        }

    async def execute(self, **kwargs) -> ToolResult:
        """
        执行地理编码，将地名转换为经纬度

        Args:
            address: 地址或地名（必需）
            city: 指定城市（可选）

        Returns:
            ToolResult: 包含经纬度信息的结果
        """
        address = kwargs.get("address")
        city = kwargs.get("city")

        logger.info(f"地理编码查询 - 地址: {address}, 城市: {city if city else '未指定'}")

        # 构造请求参数
        params = {
            "key": self.amap_key,
            "address": address,
            "output": "JSON"
        }
        if city:
            params["city"] = city

        try:
            # 发送请求
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # 检查 API 返回状态
            if data.get("status") == "1":
                geocodes = data.get("geocodes", [])

                if geocodes and len(geocodes) > 0:
                    # 获取第一个匹配结果
                    geocode = geocodes[0]
                    location_str = geocode.get("location")

                    if location_str:
                        # 高德返回格式: "经度,纬度"
                        lng, lat = location_str.split(",")
                        longitude = float(lng)
                        latitude = float(lat)

                        result_data = {
                            "address": address,
                            "formatted_address": geocode.get("formatted_address", address),
                            "longitude": longitude,
                            "latitude": latitude,
                            "province": geocode.get("province", ""),
                            "city": geocode.get("city", ""),
                            "district": geocode.get("district", ""),
                            "level": geocode.get("level", "")
                        }

                        logger.info(f"地理编码成功 - {address} → ({longitude}, {latitude})")

                        return ToolResult(
                            success=True,
                            data=result_data,
                            metadata={
                                "source": "amap",
                                "api": "geocode"
                            }
                        )
                    else:
                        error_msg = f"未能解析地址 '{address}' 的坐标信息"
                        logger.warning(error_msg)
                        return ToolResult(
                            success=False,
                            data=None,
                            error=error_msg
                        )
                else:
                    error_msg = f"未找到地址 '{address}' 的编码信息"
                    logger.warning(error_msg)
                    return ToolResult(
                        success=False,
                        data=None,
                        error=error_msg
                    )
            else:
                error_info = data.get("info", "未知错误")
                error_msg = f"高德地图 API 请求失败: {error_info}"
                logger.error(error_msg)
                return ToolResult(
                    success=False,
                    data=None,
                    error=error_msg
                )

        except requests.exceptions.Timeout:
            error_msg = "请求超时，请稍后重试"
            logger.error(error_msg)
            return ToolResult(success=False, data=None, error=error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求错误: {str(e)}"
            logger.error(error_msg)
            return ToolResult(success=False, data=None, error=error_msg)

        except Exception as e:
            error_msg = f"地理编码处理错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return ToolResult(success=False, data=None, error=error_msg)


if __name__ == "__main__":
    """测试地理编码工具"""
    import asyncio

    async def test():
        tool = LocationTool()

        test_cases = [
            {"address": "北京"},
            {"address": "上海东方明珠"},
            {"address": "清华大学"},
            {"address": "深圳市南山区"},
            {"address": "伦敦"},  # 测试国外地名
        ]

        for test_case in test_cases:
            print(f"\n测试: {test_case}")
            result = await tool.safe_execute(**test_case)

            if result.success:
                data = result.data
                print(f"✅ 成功:")
                print(f"   地址: {data['formatted_address']}")
                print(f"   经度: {data['longitude']}")
                print(f"   纬度: {data['latitude']}")
                print(f"   省份: {data.get('province', 'N/A')}")
                print(f"   城市: {data.get('city', 'N/A')}")
            else:
                print(f"❌ 失败: {result.error}")

    asyncio.run(test())
