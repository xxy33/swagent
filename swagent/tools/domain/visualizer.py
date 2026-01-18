"""
数据可视化工具
用于生成各类图表，支持固废数据的可视化展示
"""
from typing import List, Dict, Any
import json
import base64
from io import BytesIO

from swagent.tools.base_tool import (
    BaseTool,
    ToolCategory,
    ToolParameter,
    ToolResult
)
from swagent.utils.logger import get_logger


logger = get_logger(__name__)


class Visualizer(BaseTool):
    """
    数据可视化工具

    支持生成各种类型的图表
    使用matplotlib和plotly生成图表
    """

    @property
    def name(self) -> str:
        return "visualizer"

    @property
    def description(self) -> str:
        return "生成数据可视化图表，支持柱状图、折线图、饼图、散点图等多种图表类型"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.VISUALIZATION

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="chart_type",
                type="string",
                description="图表类型",
                required=True,
                enum=["bar", "line", "pie", "scatter", "histogram"]
            ),
            ToolParameter(
                name="data",
                type="object",
                description="图表数据，格式取决于图表类型",
                required=True
            ),
            ToolParameter(
                name="title",
                type="string",
                description="图表标题",
                required=False,
                default="Chart"
            ),
            ToolParameter(
                name="xlabel",
                type="string",
                description="X轴标签",
                required=False,
                default=""
            ),
            ToolParameter(
                name="ylabel",
                type="string",
                description="Y轴标签",
                required=False,
                default=""
            ),
            ToolParameter(
                name="output_format",
                type="string",
                description="输出格式",
                required=False,
                default="base64",
                enum=["base64", "file", "html"]
            )
        ]

    def get_return_description(self) -> str:
        return "返回图表数据，格式取决于output_format参数"

    def get_examples(self) -> List[Dict]:
        return [
            {
                "input": {
                    "chart_type": "bar",
                    "data": {
                        "labels": ["填埋", "焚烧", "堆肥", "回收"],
                        "values": [580, 450, 125, -800]
                    },
                    "title": "不同处理方式的碳排放",
                    "ylabel": "kg CO2 eq/ton"
                },
                "output": {
                    "chart_type": "bar",
                    "format": "base64",
                    "data": "iVBORw0KGgo..."
                }
            }
        ]

    async def execute(self, **kwargs) -> ToolResult:
        """生成可视化图表"""
        chart_type = kwargs["chart_type"]
        data = kwargs["data"]
        title = kwargs.get("title", "Chart")
        xlabel = kwargs.get("xlabel", "")
        ylabel = kwargs.get("ylabel", "")
        output_format = kwargs.get("output_format", "base64")

        logger.info(f"生成图表 - 类型: {chart_type}, 标题: {title}")

        try:
            # 尝试导入matplotlib
            try:
                import matplotlib
                matplotlib.use('Agg')  # 非GUI后端
                import matplotlib.pyplot as plt
                plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']  # 支持中文
                plt.rcParams['axes.unicode_minus'] = False
                has_matplotlib = True
            except ImportError:
                has_matplotlib = False
                logger.warning("matplotlib未安装，将返回图表配置")

            if not has_matplotlib:
                # 如果没有matplotlib，返回图表配置
                return ToolResult(
                    success=True,
                    data={
                        "chart_type": chart_type,
                        "config": {
                            "title": title,
                            "xlabel": xlabel,
                            "ylabel": ylabel,
                            "data": data
                        },
                        "note": "matplotlib not installed, returning chart configuration only"
                    }
                )

            # 生成图表
            fig, ax = plt.subplots(figsize=(10, 6))

            if chart_type == "bar":
                result = self._create_bar_chart(ax, data, title, xlabel, ylabel)
            elif chart_type == "line":
                result = self._create_line_chart(ax, data, title, xlabel, ylabel)
            elif chart_type == "pie":
                result = self._create_pie_chart(ax, data, title)
            elif chart_type == "scatter":
                result = self._create_scatter_chart(ax, data, title, xlabel, ylabel)
            elif chart_type == "histogram":
                result = self._create_histogram(ax, data, title, xlabel, ylabel)
            else:
                plt.close(fig)
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unsupported chart type: {chart_type}"
                )

            # 输出图表
            if output_format == "base64":
                # 转换为base64
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
                buffer.seek(0)
                image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
                plt.close(fig)

                return ToolResult(
                    success=True,
                    data={
                        "chart_type": chart_type,
                        "format": "base64",
                        "data": image_base64,
                        "title": title
                    }
                )

            elif output_format == "file":
                # 保存为文件
                filename = f"chart_{chart_type}.png"
                plt.savefig(filename, dpi=100, bbox_inches='tight')
                plt.close(fig)

                return ToolResult(
                    success=True,
                    data={
                        "chart_type": chart_type,
                        "format": "file",
                        "filename": filename,
                        "title": title
                    }
                )

            else:  # html
                plt.close(fig)
                return ToolResult(
                    success=False,
                    data=None,
                    error="HTML output format not implemented yet"
                )

        except Exception as e:
            logger.error(f"可视化异常: {str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                data=None,
                error=f"Visualization error: {str(e)}"
            )

    def _create_bar_chart(self, ax, data, title, xlabel, ylabel):
        """创建柱状图"""
        labels = data.get("labels", [])
        values = data.get("values", [])

        ax.bar(labels, values)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)

    def _create_line_chart(self, ax, data, title, xlabel, ylabel):
        """创建折线图"""
        x = data.get("x", [])
        y = data.get("y", [])

        ax.plot(x, y, marker='o')
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)

    def _create_pie_chart(self, ax, data, title):
        """创建饼图"""
        labels = data.get("labels", [])
        values = data.get("values", [])

        ax.pie(values, labels=labels, autopct='%1.1f%%')
        ax.set_title(title)

    def _create_scatter_chart(self, ax, data, title, xlabel, ylabel):
        """创建散点图"""
        x = data.get("x", [])
        y = data.get("y", [])

        ax.scatter(x, y)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)

    def _create_histogram(self, ax, data, title, xlabel, ylabel):
        """创建直方图"""
        values = data.get("values", [])
        bins = data.get("bins", 10)

        ax.hist(values, bins=bins, edgecolor='black')
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)
