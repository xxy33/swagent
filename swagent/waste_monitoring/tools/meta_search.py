"""
秘塔搜索API封装
用于获取城市固废管理相关政策和新闻
"""
import aiohttp
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from swagent.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SearchResult:
    """搜索结果"""
    title: str
    url: str
    snippet: str
    source: str


class MetaSearch:
    """秘塔搜索API封装"""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        初始化搜索客户端

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
            return config.get("waste_monitoring.meta_search.api_url", "https://metaso.cn/api/search")
        except Exception:
            return "https://metaso.cn/api/search"

    def _get_default_key(self) -> Optional[str]:
        """获取默认API密钥"""
        from swagent.utils.config import get_config
        try:
            config = get_config()
            return config.get("waste_monitoring.meta_search.api_key")
        except Exception:
            return None

    async def search(
        self,
        query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        执行搜索

        Args:
            query: 搜索查询
            max_results: 最大结果数

        Returns:
            搜索结果列表
        """
        logger.info(f"执行秘塔搜索: {query}")

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Content-Type": "application/json"}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                payload = {
                    "query": query,
                    "max_results": max_results
                }

                async with session.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        logger.warning(f"秘塔搜索API错误: {response.status}")
                        return await self._mock_search(query)

                    result = await response.json()
                    return self._parse_results(result)

        except Exception as e:
            logger.warning(f"秘塔搜索失败，使用模拟数据: {e}")
            return await self._mock_search(query)

    async def _mock_search(self, query: str) -> List[Dict[str, Any]]:
        """模拟搜索结果"""
        logger.info("使用模拟搜索结果")

        # 根据查询内容返回模拟结果
        if "固废" in query or "垃圾" in query:
            return [
                {
                    "title": f"《城市固体废物污染环境防治法》解读",
                    "url": "https://example.com/policy/1",
                    "snippet": "城市固体废物的处理应遵循减量化、资源化、无害化原则...",
                    "source": "政策法规"
                },
                {
                    "title": f"2024年城市生活垃圾分类工作进展报告",
                    "url": "https://example.com/report/1",
                    "snippet": "全国城市生活垃圾分类覆盖率持续提升...",
                    "source": "新闻资讯"
                },
                {
                    "title": "建筑垃圾资源化利用技术指南",
                    "url": "https://example.com/tech/1",
                    "snippet": "建筑垃圾经过破碎、筛分后可用于制备再生骨料...",
                    "source": "技术文档"
                },
                {
                    "title": "非法倾倒固体废物案例通报",
                    "url": "https://example.com/case/1",
                    "snippet": "某企业非法倾倒工业固体废物被依法处罚...",
                    "source": "执法通报"
                },
                {
                    "title": "智慧城市固废管理系统建设方案",
                    "url": "https://example.com/solution/1",
                    "snippet": "利用物联网、AI等技术实现固废全生命周期管理...",
                    "source": "行业方案"
                }
            ]
        else:
            return [
                {
                    "title": f"关于'{query}'的搜索结果",
                    "url": "https://example.com/search/1",
                    "snippet": f"找到与'{query}'相关的内容...",
                    "source": "网络搜索"
                }
            ]

    def _parse_results(self, result: Dict) -> List[Dict[str, Any]]:
        """解析API响应"""
        results = result.get("results", result.get("data", []))
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", r.get("link", "")),
                "snippet": r.get("snippet", r.get("description", "")),
                "source": r.get("source", "未知来源")
            }
            for r in results
        ]


async def meta_search(
    query: str,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    便捷函数：执行秘塔搜索

    Args:
        query: 搜索查询
        api_url: API地址 (可选)
        api_key: API密钥 (可选)
        max_results: 最大结果数

    Returns:
        搜索结果列表
    """
    client = MetaSearch(api_url=api_url, api_key=api_key)
    return await client.search(query, max_results)
