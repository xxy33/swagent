"""
生命周期评估(LCA)分析工具
用于评估固体废物管理系统的环境影响
"""
from typing import List, Dict
from dataclasses import dataclass

from swagent.tools.base_tool import (
    BaseTool,
    ToolCategory,
    ToolParameter,
    ToolResult
)
from swagent.utils.logger import get_logger


logger = get_logger(__name__)


class LCAAnalyzer(BaseTool):
    """
    生命周期评估分析工具

    评估固体废物管理系统从摇篮到坟墓的环境影响
    包括气候变化、能源消耗、水消耗等影响类别
    """

    # LCA影响因子数据库（简化版）
    # 实际应用中应使用标准LCA数据库如Ecoinvent
    IMPACT_FACTORS = {
        "landfill": {
            "climate_change": 580,  # kg CO2 eq/ton
            "energy_consumption": 50,  # MJ/ton
            "water_consumption": 10,  # m3/ton
            "land_use": 5,  # m2*year/ton
        },
        "incineration": {
            "climate_change": 450,
            "energy_consumption": -500,  # 能源回收为负值
            "water_consumption": 20,
            "land_use": 0.5,
        },
        "composting": {
            "climate_change": 125,
            "energy_consumption": 100,
            "water_consumption": 30,
            "land_use": 2,
        },
        "recycling": {
            "climate_change": -800,  # 避免的排放
            "energy_consumption": -1500,
            "water_consumption": 15,
            "land_use": 0.1,
        }
    }

    @property
    def name(self) -> str:
        return "lca_analyzer"

    @property
    def description(self) -> str:
        return "执行生命周期评估(LCA)分析，评估固体废物处理系统的多维环境影响"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.DOMAIN

    def get_parameters(self) -> List[ToolParameter]:
        return [
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
                name="impact_categories",
                type="array",
                description="要评估的影响类别",
                required=False,
                items={
                    "type": "string",
                    "enum": ["climate_change", "energy_consumption",
                             "water_consumption", "land_use"]
                }
            ),
            ToolParameter(
                name="functional_unit",
                type="string",
                description="功能单位描述",
                required=False,
                default="1 ton waste treatment"
            )
        ]

    def get_return_description(self) -> str:
        return "返回包含各影响类别评估结果的字典，以及综合评分"

    def get_examples(self) -> List[Dict]:
        return [
            {
                "input": {
                    "treatment_method": "recycling",
                    "quantity": 100,
                    "impact_categories": ["climate_change", "energy_consumption"]
                },
                "output": {
                    "treatment_method": "recycling",
                    "quantity_tonnes": 100,
                    "functional_unit": "1 ton waste treatment",
                    "impacts": {
                        "climate_change": {
                            "total": -80000,
                            "unit": "kg CO2 eq",
                            "per_ton": -800
                        },
                        "energy_consumption": {
                            "total": -150000,
                            "unit": "MJ",
                            "per_ton": -1500
                        }
                    },
                    "overall_score": "Excellent (High environmental benefit)"
                }
            }
        ]

    async def execute(self, **kwargs) -> ToolResult:
        """执行LCA分析"""
        treatment_method = kwargs["treatment_method"]
        quantity = kwargs["quantity"]
        impact_categories = kwargs.get("impact_categories", list(self.IMPACT_FACTORS[treatment_method].keys()))
        functional_unit = kwargs.get("functional_unit", "1 ton waste treatment")

        logger.info(f"LCA分析 - {treatment_method}, {quantity}吨, 影响类别: {impact_categories}")

        try:
            # 获取影响因子
            factors = self.IMPACT_FACTORS.get(treatment_method)
            if not factors:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"No LCA data available for {treatment_method}"
                )

            # 计算各影响类别
            impacts = {}
            units = {
                "climate_change": "kg CO2 eq",
                "energy_consumption": "MJ",
                "water_consumption": "m3",
                "land_use": "m2*year"
            }

            for category in impact_categories:
                if category in factors:
                    factor = factors[category]
                    total_impact = factor * quantity
                    impacts[category] = {
                        "total": round(total_impact, 2),
                        "unit": units.get(category, "unknown"),
                        "per_ton": factor
                    }

            # 计算综合评分
            overall_score = self._calculate_overall_score(treatment_method, impacts)

            result = {
                "treatment_method": treatment_method,
                "quantity_tonnes": quantity,
                "functional_unit": functional_unit,
                "impacts": impacts,
                "overall_score": overall_score,
                "interpretation": self._get_interpretation(treatment_method)
            }

            logger.info(f"LCA分析完成 - 综合评分: {overall_score}")

            return ToolResult(
                success=True,
                data=result,
                metadata={
                    "methodology": "Simplified LCA",
                    "database": "Custom impact factors",
                    "standard": "ISO 14040/14044 framework"
                }
            )

        except Exception as e:
            logger.error(f"LCA分析异常: {str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                data=None,
                error=f"LCA analysis error: {str(e)}"
            )

    def _calculate_overall_score(
        self,
        treatment_method: str,
        impacts: Dict
    ) -> str:
        """计算综合环境评分"""
        # 简化评分逻辑
        if treatment_method == "recycling":
            return "Excellent (High environmental benefit)"
        elif treatment_method == "composting":
            return "Good (Moderate environmental benefit)"
        elif treatment_method == "incineration":
            return "Fair (Some environmental benefit with energy recovery)"
        else:  # landfill
            return "Poor (Significant environmental burden)"

    def _get_interpretation(self, treatment_method: str) -> str:
        """获取结果解释"""
        interpretations = {
            "landfill": "填埋处理产生显著的温室气体排放和土地占用，环境影响较大。",
            "incineration": "焚烧处理可回收能源，但仍产生一定排放，需配备严格的污染控制设施。",
            "composting": "堆肥处理有助于有机物资源化，温室气体排放相对较低，适合有机废物。",
            "recycling": "回收处理避免了资源提取和加工的环境影响，是最优的环境选择。"
        }
        return interpretations.get(treatment_method, "")
