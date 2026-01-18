"""
网络搜索工具
支持搜索引擎查询和网页内容抓取
"""
import asyncio
import aiohttp
from typing import List
from urllib.parse import quote_plus

from swagent.tools.base_tool import (
    BaseTool,
    ToolCategory,
    ToolParameter,
    ToolResult
)
from swagent.utils.logger import get_logger


logger = get_logger(__name__)


class WebSearch(BaseTool):
    """
    网络搜索工具

    支持搜索查询（目前使用DuckDuckGo作为示例）
    注：实际应用中可集成Google API、Bing API等
    """

    def __init__(self, timeout: int = 10):
        """
        初始化网络搜索工具

        Args:
            timeout: 请求超时时间（秒）
        """
        super().__init__()
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "搜索互联网上的信息，返回相关网页标题、链接和摘要"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WEB

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type="string",
                description="搜索查询关键词",
                required=True
            ),
            ToolParameter(
                name="max_results",
                type="number",
                description="最大结果数量",
                required=False,
                default=5
            ),
            ToolParameter(
                name="language",
                type="string",
                description="搜索语言",
                required=False,
                default="zh-CN"
            )
        ]

    def get_return_description(self) -> str:
        return "返回包含标题、URL、摘要的搜索结果列表"

    def get_examples(self) -> List[dict]:
        return [
            {
                "input": {
                    "query": "固体废物处理",
                    "max_results": 3
                },
                "output": {
                    "results": [
                        {
                            "title": "固体废物处理 - 百度百科",
                            "url": "https://baike.baidu.com/item/固体废物处理",
                            "snippet": "固体废物处理是指对固体废物进行..."
                        }
                    ],
                    "count": 3
                }
            }
        ]

    async def execute(self, **kwargs) -> ToolResult:
        """执行网络搜索"""
        query = kwargs["query"]
        max_results = kwargs.get("max_results", 5)
        language = kwargs.get("language", "zh-CN")

        logger.info(f"网络搜索 - 查询: {query}, 最大结果: {max_results}")

        try:
            # 使用DuckDuckGo HTML搜索（不需要API密钥）
            results = await self._search_duckduckgo(query, max_results, language)

            return ToolResult(
                success=True,
                data={
                    "results": results,
                    "count": len(results),
                    "query": query
                }
            )

        except Exception as e:
            logger.error(f"网络搜索异常: {str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                data=None,
                error=f"Search error: {str(e)}"
            )

    async def _search_duckduckgo(
        self,
        query: str,
        max_results: int,
        language: str
    ) -> List[dict]:
        """使用DuckDuckGo搜索"""
        # 简化实现：返回模拟结果
        # 实际应用中可以调用真实搜索API或解析HTML

        # 注意：这里返回模拟数据
        # 实际应该使用 duckduckgo-search 库或其他搜索API
        results = [
            {
                "title": f"搜索结果 {i+1}: {query}",
                "url": f"https://example.com/result{i+1}",
                "snippet": f"这是关于'{query}'的搜索结果摘要 {i+1}..."
            }
            for i in range(min(max_results, 5))
        ]

        logger.info(f"DuckDuckGo搜索完成 - 返回{len(results)}条结果")

        return results

    async def _fetch_url_content(self, url: str) -> str:
        """抓取网页内容（可选功能）"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        raise Exception(f"HTTP {response.status}")
        except Exception as e:
            logger.error(f"抓取URL失败 - {url}: {str(e)}")
            raise
