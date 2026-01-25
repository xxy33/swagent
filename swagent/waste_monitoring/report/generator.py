"""
报告生成器 - 生成城市固废综合监管报告
支持使用 LLM (wuyu-30b) 生成智能报告
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from swagent.utils.logger import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    """报告生成器"""

    def __init__(
        self,
        llm_base_url: Optional[str] = None,
        llm_api_key: Optional[str] = None,
        llm_model: Optional[str] = None
    ):
        """
        初始化报告生成器

        Args:
            llm_base_url: 文本模型 API 地址
            llm_api_key: 文本模型 API 密钥
            llm_model: 文本模型名称 (如 wuyu-30b)
        """
        self.llm_base_url = llm_base_url
        self.llm_api_key = llm_api_key
        self.llm_model = llm_model
        self._llm_client = None

    async def _get_llm_client(self):
        """获取 LLM 客户端"""
        if self._llm_client is None and self.llm_base_url and self.llm_api_key:
            try:
                from swagent.llm.openai_client import OpenAIClient
                from swagent.llm.base_llm import LLMConfig

                config = LLMConfig(
                    provider="openai",
                    base_url=self.llm_base_url,
                    api_key=self.llm_api_key,
                    model=self.llm_model or "wuyu-30b"
                )
                self._llm_client = OpenAIClient(config=config)
                logger.info(f"报告生成 LLM 客户端初始化成功: {self.llm_model}")
            except Exception as e:
                logger.warning(f"LLM 客户端初始化失败: {e}")
        return self._llm_client

    async def generate(self, state: Dict[str, Any]) -> str:
        """生成综合监管报告"""
        report_data = self._prepare_report_data(state)

        # 尝试使用 LLM 生成智能分析
        llm_analysis = await self._generate_llm_analysis(report_data)
        report_data["llm_analysis"] = llm_analysis

        report = self._generate_detailed_report(report_data)
        return report

    async def _generate_llm_analysis(self, data: Dict[str, Any]) -> Optional[str]:
        """使用 LLM 生成智能分析"""
        client = await self._get_llm_client()
        if client is None:
            return None

        try:
            # 构建提示词
            prompt = self._build_analysis_prompt(data)

            messages = [
                {
                    "role": "system",
                    "content": "你是一位城市环境监测专家，擅长分析固体废物监测数据并提供专业的风险评估和整改建议。请用专业、简洁的语言回答。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            response = await client.chat(messages, temperature=0.7, max_tokens=2000)
            logger.info("LLM 智能分析生成成功")
            return response.content

        except Exception as e:
            logger.warning(f"LLM 分析生成失败: {e}")
            return None

    def _build_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """构建分析提示词"""
        weather_info = ""
        if data.get("weather_data"):
            wd = data["weather_data"]
            if isinstance(wd, dict) and "data" in wd:
                weather_info = f"\n天气数据 (2024年9月1日): {wd['data']}"

        return f"""请根据以下固废监测数据，生成一份专业的分析报告摘要：

## 监测基本信息
- 城市: {data['city_name']}
- 监测日期: {data['monitoring_date']}
- 分析图块总数: {data['total_tiles']}

## 检测结果
- 垃圾堆存点: {data['waste_count']} 处
- 清洁区域: {data['clean_count']} 处
- 检测失败: {data['error_count']} 处
- 检出率: {data['detection_rate']*100:.2f}%
{weather_info}

## 垃圾堆存点详情
{self._format_waste_sites_for_prompt(data['waste_sites'][:5])}

请提供：
1. 整体环境状况评估（2-3句话）
2. 主要风险点分析
3. 具体整改建议（分短期、中期、长期）
4. 后续监测建议

请用简洁专业的语言，直接输出分析内容。"""

    def _format_waste_sites_for_prompt(self, waste_sites: List[Dict]) -> str:
        """格式化垃圾堆存点信息用于提示词"""
        if not waste_sites:
            return "无垃圾堆存点"

        lines = []
        for i, site in enumerate(waste_sites, 1):
            desc = site.get("description", "无描述")[:100]
            lines.append(f"{i}. {site.get('tile_id', '未知')}: {desc}")
        return "\n".join(lines)

    def _prepare_report_data(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """准备报告数据"""
        stats = state.get("statistics", {})

        return {
            "city_name": state.get("city_name", "未知城市"),
            "monitoring_date": state.get("monitoring_date", datetime.now().strftime("%Y-%m-%d")),
            "total_tiles": stats.get("total_tiles", 0),
            "waste_count": stats.get("waste_count", 0),
            "clean_count": stats.get("clean_count", 0),
            "error_count": stats.get("error_count", 0),
            "detection_rate": stats.get("detection_rate", 0),
            "waste_rate": stats.get("waste_rate", 0),
            "waste_sites": state.get("waste_sites", []),
            "weather_data": state.get("weather_data"),
            "search_results": state.get("search_results", []),
            "historical_data": state.get("historical_data"),
            "processing_log": state.get("processing_log", []),
            "errors": state.get("errors", []),
            "start_time": state.get("start_time"),
            "end_time": state.get("end_time", datetime.now().isoformat()),
            "output_dir": state.get("output_dir", "./output"),
            "mode": state.get("mode", "unknown"),
            "tile_size": state.get("tile_size", 512),
            "tile_overlap": state.get("tile_overlap", 64)
        }

    def _generate_detailed_report(self, data: Dict[str, Any]) -> str:
        """生成详细报告"""
        report = self._generate_cover_page(data)
        report += self._generate_table_of_contents(data)
        report += self._generate_executive_summary(data)
        report += self._generate_weather_section(data)  # 新增：天气信息
        report += self._generate_llm_analysis_section(data)  # 新增：LLM智能分析
        report += self._generate_methodology(data)
        report += self._generate_monitoring_overview(data)
        report += self._generate_detection_results(data)
        report += self._generate_waste_sites_chapter(data)
        report += self._generate_sample_showcase(data)  # 样例展示
        report += self._generate_risk_assessment(data)
        report += self._generate_recommendations(data)
        report += self._generate_appendix(data)
        report += self._generate_footer(data)
        return report

    def _generate_weather_section(self, data: Dict[str, Any]) -> str:
        """生成天气信息章节"""
        weather = data.get("weather_data")
        if not weather:
            return ""

        section = """
## 监测期间天气状况

"""
        if isinstance(weather, dict):
            if "data" in weather:
                wd = weather["data"]
                if isinstance(wd, dict) and "data" in wd:
                    weather_info = wd["data"]
                    section += f"""
| 项目 | 数值 |
|------|------|
| 查询时间 | 2024年9月1日 12:00 |
| 温度 | {weather_info.get('temperature_2m', 'N/A')} °C |
| 相对湿度 | {weather_info.get('relative_humidity_2m', 'N/A')} % |
| 降水量 | {weather_info.get('precipitation', 'N/A')} mm |
| 风速 | {weather_info.get('wind_speed_10m', 'N/A')} km/h |

"""
            if "coordinates" in weather:
                coords = weather["coordinates"]
                section += f"*监测坐标: ({coords.get('latitude', 'N/A')}, {coords.get('longitude', 'N/A')})*\n\n"

        section += "---\n\n"
        return section

    def _generate_llm_analysis_section(self, data: Dict[str, Any]) -> str:
        """生成 LLM 智能分析章节"""
        llm_analysis = data.get("llm_analysis")
        if not llm_analysis:
            return ""

        return f"""
## 智能分析报告

*以下内容由 AI 模型自动生成*

{llm_analysis}

---

"""

    def _generate_cover_page(self, data: Dict[str, Any]) -> str:
        """生成封面"""
        return f"""
# 城市固体废物智能监测综合监管报告

---

## {data['city_name']}

### 监测日期：{data['monitoring_date']}

---

**报告编号**: WM-{data['monitoring_date'].replace('-', '')}-{data['city_name'][:2]}

**编制单位**: 城市固废智能监测系统

---

"""

    def _generate_table_of_contents(self, data: Dict[str, Any]) -> str:
        """生成目录"""
        return """
## 目录

1. [执行摘要](#执行摘要)
2. [监测方法](#监测方法)
3. [监测概况](#监测概况)
4. [检测结果](#检测结果)
5. [垃圾堆存点详情](#垃圾堆存点详情)
6. [样例展示](#样例展示)
7. [风险评估](#风险评估)
8. [整改建议](#整改建议)
9. [附录](#附录)

---

"""

    def _generate_executive_summary(self, data: Dict[str, Any]) -> str:
        """生成执行摘要"""
        detection_rate = data['detection_rate']
        if detection_rate > 0.05:
            risk_level = "高风险"
        elif detection_rate > 0.02:
            risk_level = "中风险"
        else:
            risk_level = "低风险"

        return f"""
## 执行摘要

### 核心数据

| 指标 | 数值 |
|------|------|
| 分析图块总数 | **{data['total_tiles']}** |
| 垃圾堆存点 | **{data['waste_count']}** 处 |
| 清洁区域 | **{data['clean_count']}** 处 |
| 检测失败 | **{data['error_count']}** 处 |
| 检出率 | **{detection_rate*100:.2f}%** |
| 风险等级 | **{risk_level}** |

### 主要发现

"""
        + self._generate_key_findings(data) + """

---

"""

    def _generate_key_findings(self, data: Dict[str, Any]) -> str:
        """生成主要发现"""
        findings = []

        if data['waste_count'] > 0:
            findings.append(f"- 发现 **{data['waste_count']}** 处垃圾堆存点")
        else:
            findings.append("- 未发现垃圾堆存问题，区域环境状况良好")

        if data['detection_rate'] > 0.03:
            findings.append("- 检出率偏高，需重点关注")

        if data['error_count'] > 0:
            findings.append(f"- {data['error_count']} 处图块检测失败，建议复查")

        return "\n".join(findings)

    def _generate_methodology(self, data: Dict[str, Any]) -> str:
        """生成监测方法"""
        return f"""
## 监测方法

### 技术架构

本项目采用大模型视觉语言分析技术：

1. **图像切割**：将大幅遥感影像切割为 {data['tile_size']}x{data['tile_size']} 像素的图块
2. **AI 检测**：使用视觉语言模型分析每个图块
3. **结果输出**：JSON 格式输出，包含 label、description、boundingbox

### 分类标准

| 分类 | 判定条件 |
|------|----------|
| **垃圾堆存** | label=1，检测到垃圾 |
| **清洁区域** | label=0，未检测到垃圾 |
| **检测失败** | label=-1，API 调用失败 |

---

"""

    def _generate_monitoring_overview(self, data: Dict[str, Any]) -> str:
        """生成监测概况"""
        processing_time = "未知"
        if data.get('start_time') and data.get('end_time'):
            try:
                start = datetime.fromisoformat(data['start_time'])
                end = datetime.fromisoformat(data['end_time'])
                duration = end - start
                minutes = duration.seconds // 60
                seconds = duration.seconds % 60
                processing_time = f"{minutes}分{seconds}秒"
            except:
                pass

        return f"""
## 监测概况

| 项目 | 内容 |
|------|------|
| 监测城市 | {data['city_name']} |
| 监测日期 | {data['monitoring_date']} |
| 分析图块数 | {data['total_tiles']} 张 |
| 处理耗时 | {processing_time} |
| 运行模式 | {data['mode']} |

---

"""

    def _generate_detection_results(self, data: Dict[str, Any]) -> str:
        """生成检测结果"""
        total = data['total_tiles']
        waste = data['waste_count']
        clean = data['clean_count']
        error = data['error_count']

        waste_pct = (waste / total * 100) if total > 0 else 0
        clean_pct = (clean / total * 100) if total > 0 else 0
        error_pct = (error / total * 100) if total > 0 else 0

        return f"""
## 检测结果

### 统计汇总

| 类别 | 数量 | 占比 |
|------|------|------|
| 垃圾堆存点 | {waste} | {waste_pct:.2f}% |
| 清洁区域 | {clean} | {clean_pct:.2f}% |
| 检测失败 | {error} | {error_pct:.2f}% |
| **合计** | **{total}** | **100%** |

---

"""

    def _generate_waste_sites_chapter(self, data: Dict[str, Any]) -> str:
        """生成垃圾堆存点详情章节"""
        chapter = f"""
## 垃圾堆存点详情

共发现 **{data['waste_count']}** 处垃圾堆存点。

"""
        if not data['waste_sites']:
            chapter += "*本次监测未发现垃圾堆存点*\n\n---\n\n"
            return chapter

        chapter += "### 详细清单\n\n"

        for i, site in enumerate(data['waste_sites'], 1):
            tile_id = site.get('tile_id', f'未知-{i}')
            description = site.get('description', '无描述')
            reasoning = site.get('reasoning', '')
            boundingbox = site.get('boundingbox', [])
            tile_path = site.get('tile_path', '')

            chapter += f"""
#### {i}. {tile_id}

| 项目 | 内容 |
|------|------|
| 图块ID | {tile_id} |
| 检测框数量 | {len(boundingbox)} 个 |

**AI 描述**

> {description}

**推理过程**

> {reasoning[:300]}{'...' if len(reasoning) > 300 else ''}

---

"""

        return chapter

    def _generate_sample_showcase(self, data: Dict[str, Any]) -> str:
        """生成样例展示章节"""
        chapter = """
## 样例展示

本章节展示检测到垃圾堆存的图像样例，包含原始遥感图像与处理后的标注图像对比。

"""
        waste_sites = data['waste_sites']

        if not waste_sites:
            chapter += "*本次监测未发现垃圾堆存，无样例可展示*\n\n---\n\n"
            return chapter

        # 最多展示 10 张
        display_sites = waste_sites[:10]
        total_sites = len(waste_sites)

        if total_sites > 10:
            chapter += f"*共检测到 {total_sites} 处垃圾堆存，以下展示前 10 个样例*\n\n"
        else:
            chapter += f"*共检测到 {total_sites} 处垃圾堆存，全部展示如下*\n\n"

        for i, site in enumerate(display_sites, 1):
            tile_id = site.get('tile_id', f'样例-{i}')
            tile_path = site.get('tile_path', '')
            processed_path = site.get('processed_image_path', '')
            description = site.get('description', '无描述')
            boundingbox = site.get('boundingbox', [])

            # 转换路径格式：将绝对路径转换为相对于项目根目录的路径
            # /root/swagent/output/xxx -> /output/xxx
            if tile_path:
                if tile_path.startswith('/root/swagent/'):
                    tile_path = '/' + tile_path.replace('/root/swagent/', '')
                elif not tile_path.startswith('/'):
                    tile_path = '/' + tile_path

            if processed_path:
                if processed_path.startswith('/root/swagent/'):
                    processed_path = '/' + processed_path.replace('/root/swagent/', '')
                elif not processed_path.startswith('/'):
                    processed_path = '/' + processed_path

            chapter += f"""
### 样例 {i}: {tile_id}

<table>
<tr>
<td width="50%" align="center">

**原始遥感图像**

![原图]({tile_path})

</td>
<td width="50%" align="center">

**处理后标注图像**

"""
            if processed_path:
                chapter += f"![标注]({processed_path})\n"
            else:
                chapter += "*（处理后图像未生成）*\n"

            chapter += f"""
</td>
</tr>
</table>

**检测信息**
- 检测框数量: {len(boundingbox)} 个
- Bounding Box: {boundingbox if boundingbox else '无'}

**AI 分析描述**

> {description}

---

"""

        return chapter

    def _generate_risk_assessment(self, data: Dict[str, Any]) -> str:
        """生成风险评估"""
        risk_score = 0

        if data['waste_count'] > 10:
            risk_score += 40
        elif data['waste_count'] > 5:
            risk_score += 25
        elif data['waste_count'] > 0:
            risk_score += 10

        if data['detection_rate'] > 0.05:
            risk_score += 30
        elif data['detection_rate'] > 0.02:
            risk_score += 15

        if risk_score >= 50:
            risk_level = "高风险"
        elif risk_score >= 25:
            risk_level = "中风险"
        else:
            risk_level = "低风险"

        return f"""
## 风险评估

### 综合评分

| 项目 | 评分 |
|------|------|
| 风险分数 | **{risk_score}** 分 |
| 风险等级 | **{risk_level}** |

### 潜在影响

- 土壤污染风险
- 水体污染风险
- 大气污染风险

---

"""

    def _generate_recommendations(self, data: Dict[str, Any]) -> str:
        """生成整改建议"""
        return f"""
## 整改建议

### 短期措施（1-2周）

1. 对 {data['waste_count']} 处垃圾堆存点进行现场核查
2. 拍照取证，记录堆存规模
3. 识别责任主体

### 中期措施（1-3个月）

1. 分类清理处置
2. 场地整治修复
3. 完善巡查机制

### 长期措施（3-12个月）

1. 建立常态化监测机制
2. 完善固废管理信息平台
3. 加强宣传教育

---

"""

    def _generate_appendix(self, data: Dict[str, Any]) -> str:
        """生成附录"""
        appendix = """
## 附录

### 处理日志

```
"""
        for log in data.get('processing_log', [])[-15:]:
            appendix += f"{log}\n"

        appendix += """
```

### 错误记录

"""
        errors = data.get('errors', [])
        if errors:
            for i, err in enumerate(errors[:10], 1):
                appendix += f"{i}. {err[:100]}\n"
        else:
            appendix += "*无错误*\n"

        appendix += "\n---\n\n"
        return appendix

    def _generate_footer(self, data: Dict[str, Any]) -> str:
        """生成页脚"""
        return f"""
---

*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

*城市固废智能监测系统*
"""


async def generate_monitoring_report(
    state: Dict[str, Any],
    llm_base_url: Optional[str] = None,
    llm_api_key: Optional[str] = None,
    llm_model: Optional[str] = None
) -> str:
    """
    便捷函数：生成监管报告

    Args:
        state: 工作流状态
        llm_base_url: 文本模型 API 地址
        llm_api_key: 文本模型 API 密钥
        llm_model: 文本模型名称 (如 wuyu-30b)

    Returns:
        生成的报告内容
    """
    generator = ReportGenerator(
        llm_base_url=llm_base_url,
        llm_api_key=llm_api_key,
        llm_model=llm_model
    )
    return await generator.generate(state)
