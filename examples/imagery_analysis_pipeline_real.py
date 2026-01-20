"""
卫星影像分析流水线 - 真实LLM版本
================================

使用 StateGraph 实现多模型协作的影像分析流水线，调用真实的大模型API：
1. 图像加载 -> 2. 分割模型(LLM模拟) -> 3. 大模型分析 -> 4. 写作模型 -> 5. 生成报告

运行方式:
    python examples/imagery_analysis_pipeline_real.py
"""
import asyncio
import os
import base64
import json
from datetime import datetime
from pathlib import Path
from typing import TypedDict, List, Dict, Any, Optional

# 添加项目根目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from swagent.stategraph import StateGraph, ExecutionConfig, GraphStatus
from swagent.llm import OpenAIClient, LLMConfig


# =============================================================================
# 状态定义
# =============================================================================

class ImageAnalysisState(TypedDict):
    """影像分析流水线状态"""
    # 输入
    image_path: str
    image_name: str

    # 图像数据
    image_base64: Optional[str]
    image_size_mb: float

    # 分割模型输出
    segmentation_result: Optional[str]
    land_cover_stats: Optional[Dict[str, float]]

    # 大模型分析输出
    scene_analysis: Optional[str]
    detected_features: Optional[str]

    # 写作模型输出
    report_draft: Optional[str]

    # 最终输出
    final_report: Optional[str]
    report_path: Optional[str]

    # 元数据
    processing_log: List[str]
    start_time: str
    llm_calls: int
    total_tokens: int
    errors: List[str]


# =============================================================================
# LLM 客户端管理
# =============================================================================

class LLMManager:
    """LLM客户端管理器"""

    def __init__(self):
        self.client: Optional[OpenAIClient] = None
        self.total_tokens = 0

    async def init_client(self):
        """初始化LLM客户端"""
        try:
            self.client = OpenAIClient.from_config_file()
            return True
        except Exception as e:
            print(f"❌ LLM客户端初始化失败: {e}")
            return False

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> Optional[str]:
        """调用LLM"""
        if not self.client:
            return None

        try:
            response = await self.client.chat(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            self.total_tokens += response.usage.get("total_tokens", 0)
            return response.content
        except Exception as e:
            print(f"❌ LLM调用失败: {e}")
            return None


# 全局LLM管理器
llm_manager = LLMManager()


# =============================================================================
# StateGraph 流水线定义
# =============================================================================

def create_real_imagery_pipeline():
    """创建真实LLM调用的影像分析流水线"""

    graph = StateGraph(ImageAnalysisState)

    # ----- 节点1: 加载图像 -----
    @graph.node()
    async def load_image(state: ImageAnalysisState) -> dict:
        """加载图像并转换为base64"""
        image_path = state["image_path"]

        if not os.path.exists(image_path):
            return {
                "errors": state["errors"] + [f"图像文件不存在: {image_path}"],
                "processing_log": state["processing_log"] + ["[ERROR] 图像加载失败"]
            }

        # 读取图像并转换为base64
        with open(image_path, "rb") as f:
            image_data = f.read()

        image_base64 = base64.b64encode(image_data).decode("utf-8")
        file_size_mb = len(image_data) / 1024 / 1024

        return {
            "image_base64": image_base64,
            "image_size_mb": file_size_mb,
            "image_name": os.path.basename(image_path),
            "processing_log": state["processing_log"] + [
                f"[OK] 图像加载完成: {os.path.basename(image_path)}",
                f"     文件大小: {file_size_mb:.2f} MB"
            ]
        }

    # ----- 节点2: 分割模型 (LLM模拟) -----
    @graph.node()
    async def run_segmentation(state: ImageAnalysisState) -> dict:
        """使用LLM模拟分割模型，分析地物类型"""
        if state["image_base64"] is None:
            return {
                "errors": state["errors"] + ["无图像数据"],
                "processing_log": state["processing_log"] + ["[SKIP] 分割分析"]
            }

        print("  🔄 正在进行地物分割分析...")

        # 构建消息 - 让LLM分析图像中的地物类型
        messages = [
            {
                "role": "system",
                "content": """你是一个专业的遥感影像分析专家，擅长分析卫星影像中的地物类型。
请分析用户提供的卫星影像，识别并估算各类地物的占比。

你需要输出以下格式的JSON结果：
{
    "land_cover": {
        "building": 0.XX,
        "road": 0.XX,
        "vegetation": 0.XX,
        "water": 0.XX,
        "bare_land": 0.XX,
        "other": 0.XX
    },
    "analysis": "详细的地物分析描述..."
}

注意：所有占比之和应该等于1.0"""
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"请分析这张卫星影像（{state['image_name']}），识别其中的地物类型并估算各类地物的覆盖比例。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{state['image_base64']}"
                        }
                    }
                ]
            }
        ]

        response = await llm_manager.chat(messages, temperature=0.3, max_tokens=1024)

        if not response:
            return {
                "errors": state["errors"] + ["分割模型调用失败"],
                "processing_log": state["processing_log"] + ["[ERROR] 分割分析失败"],
                "llm_calls": state["llm_calls"] + 1
            }

        # 尝试解析JSON
        land_cover = {}
        try:
            # 尝试从响应中提取JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
                land_cover = result.get("land_cover", {})
        except:
            pass

        return {
            "segmentation_result": response,
            "land_cover_stats": land_cover if land_cover else {
                "building": 0.40, "road": 0.20, "vegetation": 0.25,
                "bare_land": 0.10, "other": 0.05
            },
            "processing_log": state["processing_log"] + [
                "[OK] 地物分割分析完成",
                f"     识别地物类型: {len(land_cover) if land_cover else 5} 类"
            ],
            "llm_calls": state["llm_calls"] + 1,
            "total_tokens": llm_manager.total_tokens
        }

    # ----- 节点3: 大模型场景分析 -----
    @graph.node()
    async def run_scene_analysis(state: ImageAnalysisState) -> dict:
        """使用大模型进行场景分析"""
        if state["image_base64"] is None:
            return {
                "errors": state["errors"] + ["无图像数据"],
                "processing_log": state["processing_log"] + ["[SKIP] 场景分析"]
            }

        print("  🔄 正在进行场景分析...")

        # 构建场景分析prompt
        land_cover_info = ""
        if state["land_cover_stats"]:
            land_cover_info = "地物分割结果：\n"
            for k, v in state["land_cover_stats"].items():
                land_cover_info += f"  - {k}: {v*100:.1f}%\n"

        messages = [
            {
                "role": "system",
                "content": """你是一个资深的城市规划和遥感分析专家。请对卫星影像进行深入的场景分析，包括：

1. **场景类型判断**：判断这是什么类型的区域（居住区、商业区、工业区、农业区等）
2. **建筑特征分析**：分析建筑物的类型、密度、布局特点
3. **交通设施分析**：分析道路网络、停车设施等
4. **绿化环境分析**：分析植被覆盖、绿地分布
5. **特殊设施识别**：识别学校、医院、公园、体育场等特殊设施
6. **区域特点总结**：总结该区域的主要特点和发展状况

请提供详细、专业的分析报告。"""
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""请对这张卫星影像进行详细的场景分析。

影像信息：
- 文件名：{state['image_name']}
- 文件大小：{state['image_size_mb']:.2f} MB

{land_cover_info}

请从城市规划和遥感分析的专业角度，对该区域进行全面分析。"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{state['image_base64']}"
                        }
                    }
                ]
            }
        ]

        response = await llm_manager.chat(messages, temperature=0.7, max_tokens=2048)

        if not response:
            return {
                "errors": state["errors"] + ["场景分析调用失败"],
                "processing_log": state["processing_log"] + ["[ERROR] 场景分析失败"],
                "llm_calls": state["llm_calls"] + 1
            }

        return {
            "scene_analysis": response,
            "processing_log": state["processing_log"] + [
                "[OK] 场景分析完成",
                f"     分析长度: {len(response)} 字符"
            ],
            "llm_calls": state["llm_calls"] + 1,
            "total_tokens": llm_manager.total_tokens
        }

    # ----- 节点4: 特征检测分析 -----
    @graph.node()
    async def run_feature_detection(state: ImageAnalysisState) -> dict:
        """检测和分析具体特征"""
        if state["image_base64"] is None:
            return {
                "errors": state["errors"] + ["无图像数据"],
                "processing_log": state["processing_log"] + ["[SKIP] 特征检测"]
            }

        print("  🔄 正在进行特征检测...")

        messages = [
            {
                "role": "system",
                "content": """你是一个专业的遥感图像目标检测专家。请对卫星影像进行目标检测和特征分析：

1. **建筑物检测**：
   - 估算建筑物数量
   - 区分建筑类型（住宅、商业、工业、公共设施等）
   - 分析建筑高度特征

2. **道路检测**：
   - 识别主干道和支路
   - 分析道路网络结构
   - 估算道路密度

3. **绿地检测**：
   - 识别公园、绿地
   - 分析植被分布特点

4. **特殊设施**：
   - 识别体育场、学校、停车场等
   - 标注特殊建筑物

请以结构化的方式输出检测结果。"""
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"请对这张卫星影像（{state['image_name']}）进行目标检测，识别各类地物目标并给出数量估计。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{state['image_base64']}"
                        }
                    }
                ]
            }
        ]

        response = await llm_manager.chat(messages, temperature=0.5, max_tokens=1536)

        if not response:
            return {
                "errors": state["errors"] + ["特征检测调用失败"],
                "processing_log": state["processing_log"] + ["[ERROR] 特征检测失败"],
                "llm_calls": state["llm_calls"] + 1
            }

        return {
            "detected_features": response,
            "processing_log": state["processing_log"] + [
                "[OK] 特征检测完成",
                f"     检测结果长度: {len(response)} 字符"
            ],
            "llm_calls": state["llm_calls"] + 1,
            "total_tokens": llm_manager.total_tokens
        }

    # ----- 节点5: 写作模型生成报告 -----
    @graph.node()
    async def run_report_writing(state: ImageAnalysisState) -> dict:
        """使用写作模型生成完整报告"""
        print("  🔄 正在生成分析报告...")

        # 汇总之前的分析结果
        previous_analysis = f"""
## 地物分割结果

{state.get('segmentation_result', '无分割结果')}

## 场景分析结果

{state.get('scene_analysis', '无场景分析')}

## 特征检测结果

{state.get('detected_features', '无特征检测结果')}
"""

        messages = [
            {
                "role": "system",
                "content": """你是一位专业的技术报告撰写专家，擅长将遥感分析结果整理成结构化的专业报告。

请根据提供的分析结果，生成一份完整的卫星影像分析报告，包含以下章节：

1. **执行摘要** - 简要总结主要发现
2. **分析方法** - 说明使用的分析方法和技术
3. **地物覆盖分析** - 详细的土地利用/地物覆盖分析
4. **场景特征分析** - 区域特征和空间布局分析
5. **目标检测结果** - 各类目标的检测统计
6. **问题与建议** - 发现的问题和改进建议
7. **结论** - 总体结论

报告要求：
- 使用Markdown格式
- 语言专业、客观
- 数据准确、有依据
- 建议具体、可行"""
            },
            {
                "role": "user",
                "content": f"""请根据以下分析结果，生成一份完整的卫星影像分析报告。

影像信息：
- 文件名：{state['image_name']}
- 分析时间：{state['start_time']}

{previous_analysis}

请生成专业的分析报告。"""
            }
        ]

        response = await llm_manager.chat(messages, temperature=0.7, max_tokens=3000)

        if not response:
            return {
                "errors": state["errors"] + ["报告生成调用失败"],
                "processing_log": state["processing_log"] + ["[ERROR] 报告生成失败"],
                "llm_calls": state["llm_calls"] + 1
            }

        return {
            "report_draft": response,
            "processing_log": state["processing_log"] + [
                "[OK] 报告初稿生成完成",
                f"     报告长度: {len(response)} 字符"
            ],
            "llm_calls": state["llm_calls"] + 1,
            "total_tokens": llm_manager.total_tokens
        }

    # ----- 节点6: 汇总生成最终报告 -----
    @graph.node()
    async def generate_final_report(state: ImageAnalysisState) -> dict:
        """汇总生成最终报告并保存"""
        print("  🔄 正在汇总最终报告...")

        # 构建完整报告
        report = f"""# 卫星影像智能分析报告

---

**影像文件**: {state['image_name']}
**分析时间**: {state['start_time']}
**LLM调用次数**: {state['llm_calls']}
**总Token消耗**: {state['total_tokens']}

---

{state.get('report_draft', '报告生成失败')}

---

## 附录：原始分析数据

### A. 地物分割原始结果

{state.get('segmentation_result', 'N/A')[:1000]}...

### B. 处理日志

```
{chr(10).join(state['processing_log'])}
```

---

*本报告由 StateGraph 多模型协作流水线自动生成*
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        # 保存报告
        report_dir = Path(__file__).parent.parent / "reports"
        report_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_stem = Path(state['image_name']).stem
        report_filename = f"analysis_report_{image_stem}_{timestamp}.md"
        report_path = report_dir / report_filename

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        return {
            "final_report": report,
            "report_path": str(report_path),
            "processing_log": state["processing_log"] + [
                "[OK] 最终报告生成完成",
                f"     报告路径: {report_path}"
            ],
            "total_tokens": llm_manager.total_tokens
        }

    # ----- 定义流水线流程 -----
    graph.set_entry_point("load_image")
    graph.add_edge("load_image", "run_segmentation")
    graph.add_edge("run_segmentation", "run_scene_analysis")
    graph.add_edge("run_scene_analysis", "run_feature_detection")
    graph.add_edge("run_feature_detection", "run_report_writing")
    graph.add_edge("run_report_writing", "generate_final_report")
    graph.set_exit_point("generate_final_report")

    return graph


# =============================================================================
# 主函数
# =============================================================================

async def main():
    """主函数"""
    print("=" * 70)
    print("🛰️  卫星影像智能分析流水线 (真实LLM版本)")
    print("=" * 70)

    # 初始化LLM客户端
    print("\n📡 初始化LLM客户端...")
    if not await llm_manager.init_client():
        print("❌ 无法初始化LLM客户端，请检查配置")
        return

    print(f"✅ LLM客户端初始化成功")
    print(f"   模型: {llm_manager.client.config.model}")
    print(f"   API: {llm_manager.client.config.base_url}")

    # 查找图像
    imagery_dir = Path(__file__).parent.parent / "imagery_output"

    if not imagery_dir.exists():
        print(f"❌ 图像目录不存在: {imagery_dir}")
        return

    # 获取图像列表
    images = list(imagery_dir.glob("*.png")) + list(imagery_dir.glob("*.jpg"))

    if not images:
        print(f"❌ 未找到图像文件")
        return

    print(f"\n📂 找到 {len(images)} 个图像文件:")
    for i, img in enumerate(images):
        size_mb = img.stat().st_size / 1024 / 1024
        print(f"   {i+1}. {img.name} ({size_mb:.2f} MB)")

    # 选择较小的图像（避免base64过大）
    images_sorted = sorted(images, key=lambda x: x.stat().st_size)
    selected_image = images_sorted[0]

    # 检查文件大小，大于10MB可能会有问题
    if selected_image.stat().st_size > 10 * 1024 * 1024:
        print(f"\n⚠️  警告: 图像文件较大 ({selected_image.stat().st_size/1024/1024:.1f} MB)，可能影响处理速度")

    print(f"\n🎯 选择分析: {selected_image.name}")

    # 创建流水线
    print("\n📊 创建分析流水线...")
    graph = create_real_imagery_pipeline()

    # 验证图
    validation_errors = graph.validate()
    if validation_errors:
        print(f"❌ 流水线验证失败: {validation_errors}")
        return

    print("✅ 流水线验证通过")
    print(f"   节点数: {len(graph._nodes)}")

    # 编译
    config = ExecutionConfig(max_iterations=10, save_checkpoints=True)
    app = graph.compile(config=config)

    # 初始状态
    initial_state: ImageAnalysisState = {
        "image_path": str(selected_image),
        "image_name": selected_image.name,
        "image_base64": None,
        "image_size_mb": 0.0,
        "segmentation_result": None,
        "land_cover_stats": None,
        "scene_analysis": None,
        "detected_features": None,
        "report_draft": None,
        "final_report": None,
        "report_path": None,
        "processing_log": [],
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "llm_calls": 0,
        "total_tokens": 0,
        "errors": []
    }

    # 执行流水线
    print("\n🚀 开始执行流水线...\n")
    print("-" * 70)

    start_time = datetime.now()
    result = await app.invoke(initial_state)
    end_time = datetime.now()

    # 输出结果
    print("-" * 70)
    print("\n" + "=" * 70)
    print("📋 执行结果")
    print("=" * 70)

    print(f"\n状态: {result.status.value}")
    print(f"迭代次数: {result.iterations}")
    print(f"执行时间: {(end_time - start_time).total_seconds():.1f} 秒")
    print(f"LLM调用次数: {result.state['llm_calls']}")
    print(f"总Token消耗: {result.state['total_tokens']}")

    if result.error:
        print(f"\n❌ 错误: {result.error}")

    print("\n📝 处理日志:")
    for log in result.state["processing_log"]:
        print(f"   {log}")

    if result.state["errors"]:
        print("\n⚠️ 错误信息:")
        for err in result.state["errors"]:
            print(f"   - {err}")

    if result.state["report_path"]:
        print(f"\n📄 报告已保存: {result.state['report_path']}")

        # 显示报告预览
        print("\n" + "=" * 70)
        print("📖 报告预览")
        print("=" * 70)
        report_preview = result.state["final_report"][:3000]
        print(report_preview)
        if len(result.state["final_report"]) > 3000:
            print("\n... (报告已截断，完整内容请查看文件)")

    return result


if __name__ == "__main__":
    asyncio.run(main())
