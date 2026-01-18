"""
温室气体排放计算工具
基于IPCC指南计算固体废物处理过程中的温室气体排放
"""
from typing import List, Dict

from swagent.tools.base_tool import (
    BaseTool,
    ToolCategory,
    ToolParameter,
    ToolResult
)
from swagent.utils.logger import get_logger


logger = get_logger(__name__)


class EmissionCalculator(BaseTool):
    """
    温室气体排放计算工具

    基于IPCC指南计算固体废物处理过程中的温室气体排放
    """

    # 排放因子 (kg CO2e/吨废物)
    # 数据来源: IPCC Guidelines for National Greenhouse Gas Inventories
    EMISSION_FACTORS = {
        "landfill": {
            "food_waste": 580,
            "paper": 1100,
            "wood": 850,
            "textile": 450,
            "plastic": 21,
            "glass": 8,
            "metal": 12,
            "other": 200
        },
        "incineration": {
            "food_waste": 220,
            "paper": 1400,
            "wood": 1200,
            "textile": 2100,
            "plastic": 2700,
            "glass": 5,
            "metal": 10,
            "other": 500
        },
        "composting": {
            "food_waste": 125,
            "paper": 80,
            "wood": 100,
            "garden_waste": 90
        },
        "recycling": {
            "paper": -500,
            "plastic": -1200,
            "glass": -300,
            "metal": -3000
        }
    }

    # 运输排放因子 (kg CO2e/吨/km)
    TRANSPORT_FACTOR = 0.1

    @property
    def name(self) -> str:
        return "emission_calculator"

    @property
    def description(self) -> str:
        return "计算固体废物处理过程中的温室气体排放量(kg CO2e)，支持填埋、焚烧、堆肥、回收等处理方式"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.DOMAIN

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="waste_type",
                type="string",
                description="废物类型",
                required=True,
                enum=["food_waste", "paper", "wood", "textile", "plastic",
                      "glass", "metal", "garden_waste", "other"]
            ),
            ToolParameter(
                name="treatment_method",
                type="string",
                description="处理方式",
                required=True,
                enum=["landfill", "incineration", "composting", "recycling"]
            ),
            ToolParameter(
                name="quantity",
                type="number",
                description="废物量(吨)",
                required=True
            ),
            ToolParameter(
                name="include_transport",
                type="boolean",
                description="是否包含运输排放",
                required=False,
                default=False
            ),
            ToolParameter(
                name="transport_distance",
                type="number",
                description="运输距离(km)",
                required=False,
                default=0
            )
        ]

    def get_return_description(self) -> str:
        return "返回包含排放量计算结果的字典，包括直接排放、运输排放和总排放"

    def get_examples(self) -> List[Dict]:
        return [
            {
                "input": {
                    "waste_type": "food_waste",
                    "treatment_method": "composting",
                    "quantity": 100
                },
                "output": {
                    "waste_type": "food_waste",
                    "treatment_method": "composting",
                    "quantity_tonnes": 100,
                    "emission_factor": 125,
                    "direct_emission_kgCO2e": 12500,
                    "transport_emission_kgCO2e": 0,
                    "total_emission_kgCO2e": 12500,
                    "total_emission_tCO2e": 12.5
                }
            },
            {
                "input": {
                    "waste_type": "plastic",
                    "treatment_method": "recycling",
                    "quantity": 50,
                    "include_transport": True,
                    "transport_distance": 20
                },
                "output": {
                    "waste_type": "plastic",
                    "treatment_method": "recycling",
                    "quantity_tonnes": 50,
                    "emission_factor": -1200,
                    "direct_emission_kgCO2e": -60000,
                    "transport_emission_kgCO2e": 100,
                    "total_emission_kgCO2e": -59900,
                    "total_emission_tCO2e": -59.9
                }
            }
        ]

    async def execute(self, **kwargs) -> ToolResult:
        """执行排放计算"""
        waste_type = kwargs["waste_type"]
        treatment_method = kwargs["treatment_method"]
        quantity = kwargs["quantity"]
        include_transport = kwargs.get("include_transport", False)
        transport_distance = kwargs.get("transport_distance", 0)

        logger.info(f"排放计算 - {waste_type}, {treatment_method}, {quantity}吨")

        try:
            # 获取排放因子
            method_factors = self.EMISSION_FACTORS.get(treatment_method, {})
            factor = method_factors.get(waste_type)

            if factor is None:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"No emission factor available for {waste_type} with {treatment_method}"
                )

            # 计算直接排放
            direct_emission = factor * quantity

            # 计算运输排放
            transport_emission = 0
            if include_transport and transport_distance > 0:
                transport_emission = self.TRANSPORT_FACTOR * quantity * transport_distance

            total_emission = direct_emission + transport_emission

            result = {
                "waste_type": waste_type,
                "treatment_method": treatment_method,
                "quantity_tonnes": quantity,
                "emission_factor": factor,
                "direct_emission_kgCO2e": round(direct_emission, 2),
                "transport_emission_kgCO2e": round(transport_emission, 2),
                "total_emission_kgCO2e": round(total_emission, 2),
                "total_emission_tCO2e": round(total_emission / 1000, 4)
            }

            logger.info(f"排放计算完成 - 总排放: {result['total_emission_kgCO2e']} kg CO2e")

            return ToolResult(
                success=True,
                data=result,
                metadata={
                    "source": "IPCC Guidelines adapted",
                    "methodology": "Tier 1"
                }
            )

        except Exception as e:
            logger.error(f"排放计算异常: {str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                data=None,
                error=f"Calculation error: {str(e)}"
            )
