# SWAgent API 参考文档

完整的 API 接口文档，涵盖所有模块、类和函数。

## 目录

- [LLM 接口层](#llm-接口层)
- [Agent 系统](#agent-系统)
- [工具系统](#工具系统)
- [领域增强](#领域增强)
- [工作流系统](#工作流系统)

---

## LLM 接口层

### LLMConfig

```python
@dataclass
class LLMConfig:
    """LLM 配置类"""
    provider: str          # 提供商: "openai", "local", "azure"
    model: str            # 模型名称
    api_key: str          # API密钥
    base_url: str = "https://api.openai.com/v1"  # API基础URL
    temperature: float = 0.7                      # 温度参数 (0.0-2.0)
    max_tokens: Optional[int] = None             # 最大令牌数
    timeout: int = 60                            # 超时时间(秒)
```

**参数说明:**
- `provider`: LLM 提供商，支持 "openai"、"local"、"azure"
- `model`: 模型名称，如 "gpt-4"、"gpt-3.5-turbo"
- `api_key`: API 访问密钥
- `base_url`: API 端点 URL，支持自定义本地部署地址
- `temperature`: 控制输出随机性，0.0=确定性，2.0=最随机
- `max_tokens`: 单次响应最大令牌数，None=不限制
- `timeout`: 请求超时时间（秒）

### LLMResponse

```python
@dataclass
class LLMResponse:
    """LLM 响应类"""
    content: str                              # 响应内容
    role: str = "assistant"                   # 角色
    finish_reason: Optional[str] = None       # 完成原因
    usage: Optional[Dict[str, int]] = None    # 令牌使用情况
    tool_calls: Optional[List[Dict]] = None   # 工具调用信息
```

**字段说明:**
- `content`: LLM 生成的文本内容
- `role`: 消息角色，通常为 "assistant"
- `finish_reason`: 停止原因，如 "stop"、"length"、"tool_calls"
- `usage`: 令牌使用统计，包含 prompt_tokens、completion_tokens、total_tokens
- `tool_calls`: 工具调用列表，每项包含 id、type、function

### BaseLLM

```python
class BaseLLM(ABC):
    """LLM 基类"""

    def __init__(self, config: LLMConfig):
        """初始化 LLM 客户端"""

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """发送对话请求"""

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncIterator[str]:
        """流式对话"""
```

**方法说明:**
- `chat()`: 发送对话消息，返回完整响应
- `chat_stream()`: 流式生成响应，逐块返回内容

### OpenAIClient

```python
class OpenAIClient(BaseLLM):
    """OpenAI 客户端"""

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """发送对话请求"""

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncIterator[str]:
        """流式对话"""

    async def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        tool_choice: str = "auto",
        **kwargs
    ) -> LLMResponse:
        """带工具调用的对话"""
```

**参数说明:**
- `messages`: 消息列表，格式 `[{"role": "user", "content": "..."}]`
- `temperature`: 覆盖配置中的温度参数
- `max_tokens`: 覆盖配置中的最大令牌数
- `tools`: 工具定义列表（OpenAI Function Calling 格式）
- `tool_choice`: 工具选择策略，"auto"、"none" 或 `{"type": "function", "function": {"name": "..."}}`

---

## Agent 系统

### BaseAgent

```python
class BaseAgent(ABC):
    """Agent 基类"""

    def __init__(
        self,
        name: str,
        role: str = "assistant",
        llm: Optional[BaseLLM] = None,
        system_prompt: Optional[str] = None
    ):
        """初始化 Agent"""

    @abstractmethod
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """执行任务"""

    async def chat(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """对话接口"""
```

**参数说明:**
- `name`: Agent 名称
- `role`: Agent 角色描述
- `llm`: LLM 客户端实例
- `system_prompt`: 系统提示词
- `task`: 要执行的任务描述
- `context`: 任务上下文信息
- `message`: 对话消息
- `history`: 对话历史记录

### PlannerAgent

```python
class PlannerAgent(BaseAgent):
    """规划型 Agent"""

    async def plan(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """制定计划"""

    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """执行任务（包含规划步骤）"""
```

**返回值 (plan 方法):**
```python
{
    'goal': str,           # 目标描述
    'steps': [             # 步骤列表
        {
            'step': int,
            'description': str,
            'expected_output': str
        }
    ],
    'resources_needed': List[str],  # 所需资源
    'estimated_time': str           # 预计时间
}
```

### ReActAgent

```python
class ReActAgent(BaseAgent):
    """ReAct (Reasoning + Acting) Agent"""

    def __init__(
        self,
        name: str,
        role: str = "assistant",
        llm: Optional[BaseLLM] = None,
        system_prompt: Optional[str] = None,
        max_iterations: int = 5,
        tools: Optional[List] = None
    ):
        """初始化 ReAct Agent"""

    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """执行任务（Reasoning-Acting 循环）"""
```

**参数说明:**
- `max_iterations`: 最大推理-行动循环次数
- `tools`: 可用工具列表

### MessageBus

```python
class MessageBus:
    """消息总线"""

    def __init__(self):
        """初始化消息总线"""

    async def publish(
        self,
        topic: str,
        message: AgentMessage,
        target_agent: Optional[str] = None
    ):
        """发布消息"""

    def subscribe(
        self,
        topic: str,
        agent_id: str,
        callback: Callable
    ):
        """订阅主题"""

    async def request_response(
        self,
        topic: str,
        message: AgentMessage,
        target_agent: str,
        timeout: float = 30.0
    ) -> AgentMessage:
        """请求-响应模式"""
```

**参数说明:**
- `topic`: 消息主题，如 "task.request"、"data.update"
- `message`: Agent 消息对象
- `target_agent`: 目标 Agent ID（可选，None 表示广播）
- `callback`: 消息处理回调函数
- `timeout`: 等待响应的超时时间

### Orchestrator

```python
class Orchestrator:
    """多 Agent 编排器"""

    def __init__(
        self,
        llm: Optional[BaseLLM] = None,
        message_bus: Optional[MessageBus] = None
    ):
        """初始化编排器"""

    def add_agent(self, agent: BaseAgent):
        """添加 Agent"""

    async def debate(
        self,
        topic: str,
        rounds: int = 2,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """多 Agent 辩论"""

    async def vote(
        self,
        question: str,
        options: List[str],
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """投票决策"""

    async def consensus(
        self,
        problem: str,
        context: Optional[Dict] = None,
        max_rounds: int = 3
    ) -> Dict[str, Any]:
        """共识决策"""
```

**返回值示例 (debate):**
```python
{
    'topic': str,
    'rounds': int,
    'arguments': [
        {'agent': str, 'round': int, 'argument': str}
    ],
    'summary': str
}
```

---

## 工具系统

### ToolParameter

```python
@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str                           # 参数名
    type: str                          # 参数类型
    description: str                   # 参数描述
    required: bool = False             # 是否必需
    enum: Optional[List[str]] = None   # 枚举值
    default: Optional[Any] = None      # 默认值
```

### ToolSchema

```python
class ToolSchema:
    """工具模式定义"""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: List[ToolParameter],
        category: str = "general"
    ):
        """初始化工具模式"""

    def to_openai_function(self) -> Dict[str, Any]:
        """转换为 OpenAI Function Calling 格式"""

    def to_mcp_tool(self) -> Dict[str, Any]:
        """转换为 MCP 工具格式"""
```

### ToolResult

```python
@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool                      # 是否成功
    data: Any                         # 返回数据
    error: Optional[str] = None       # 错误信息
    metadata: Optional[Dict] = None   # 元数据
```

### BaseTool

```python
class BaseTool(ABC):
    """工具基类"""

    def __init__(self):
        """初始化工具"""
        self.schema = self._create_schema()

    @abstractmethod
    def _create_schema(self) -> ToolSchema:
        """创建工具模式"""

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具"""

    def validate_parameters(self, **kwargs) -> Tuple[bool, Optional[str]]:
        """验证参数"""
```

### ToolRegistry

```python
class ToolRegistry:
    """工具注册中心"""

    def __init__(self):
        """初始化注册中心"""

    def register(self, tool: BaseTool):
        """注册工具"""

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """获取工具"""

    def list_tools(self, category: Optional[str] = None) -> List[str]:
        """列出工具"""

    async def execute_tool(
        self,
        tool_name: str,
        **kwargs
    ) -> ToolResult:
        """执行工具"""

    def to_openai_functions(
        self,
        tool_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """转换为 OpenAI Functions 格式"""

    def to_mcp_tools(
        self,
        tool_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """转换为 MCP 格式"""
```

### 内置工具

#### CodeExecutor

```python
class CodeExecutor(BaseTool):
    """代码执行工具"""

    async def execute(
        self,
        code: str,
        language: str = "python",
        timeout: int = 30
    ) -> ToolResult:
        """执行代码"""
```

**参数:**
- `code`: 要执行的代码
- `language`: 编程语言，"python" 或 "shell"
- `timeout`: 超时时间（秒）

**返回数据:**
```python
{
    'output': str,      # 标准输出
    'error': str,       # 错误输出
    'exit_code': int,   # 退出码
    'execution_time': float  # 执行时间
}
```

#### FileHandler

```python
class FileHandler(BaseTool):
    """文件处理工具"""

    async def execute(
        self,
        operation: str,
        file_path: str,
        content: Optional[str] = None,
        encoding: str = "utf-8"
    ) -> ToolResult:
        """执行文件操作"""
```

**参数:**
- `operation`: 操作类型，"read"、"write"、"append"、"delete"、"exists"
- `file_path`: 文件路径
- `content`: 文件内容（写入/追加时使用）
- `encoding`: 文件编码

#### WebSearch

```python
class WebSearch(BaseTool):
    """网络搜索工具"""

    async def execute(
        self,
        query: str,
        num_results: int = 5,
        language: str = "zh"
    ) -> ToolResult:
        """执行搜索"""
```

**参数:**
- `query`: 搜索查询
- `num_results`: 结果数量
- `language`: 搜索语言

### 领域工具

#### EmissionCalculator

```python
class EmissionCalculator(BaseTool):
    """排放计算工具"""

    async def execute(
        self,
        waste_type: str,
        treatment_method: str,
        quantity: float,
        include_transport: bool = False,
        transport_distance: float = 0
    ) -> ToolResult:
        """计算温室气体排放"""
```

**参数:**
- `waste_type`: 废物类型，如 "food_waste"、"plastic"、"paper"
- `treatment_method`: 处理方法，如 "landfill"、"incineration"、"recycling"
- `quantity`: 废物量（吨）
- `include_transport`: 是否包含运输排放
- `transport_distance`: 运输距离（公里）

**返回数据:**
```python
{
    'waste_type': str,
    'treatment_method': str,
    'quantity_tons': float,
    'treatment_emission_kgCO2e': float,
    'transport_emission_kgCO2e': float,
    'total_emission_kgCO2e': float,
    'emission_factor_used': float
}
```

#### LCAAnalyzer

```python
class LCAAnalyzer(BaseTool):
    """生命周期评估工具"""

    async def execute(
        self,
        treatment_method: str,
        quantity: float,
        impact_categories: List[str]
    ) -> ToolResult:
        """执行 LCA 分析"""
```

**参数:**
- `treatment_method`: 处理方法
- `quantity`: 数量（吨）
- `impact_categories`: 影响类别列表，如 ["climate_change", "energy_consumption"]

#### Visualizer

```python
class Visualizer(BaseTool):
    """数据可视化工具"""

    async def execute(
        self,
        chart_type: str,
        data: Dict[str, Any],
        title: str,
        save_path: Optional[str] = None
    ) -> ToolResult:
        """创建图表"""
```

**参数:**
- `chart_type`: 图表类型，"bar"、"line"、"pie"、"scatter"
- `data`: 图表数据，`{"labels": [...], "values": [...]}`
- `title`: 图表标题
- `save_path`: 保存路径（可选）

---

## 领域增强

### KnowledgeBase

```python
class KnowledgeBase:
    """固废领域知识库"""

    def __init__(self, data_dir: Optional[Path] = None):
        """初始化知识库"""

    def get_waste_category(
        self,
        category_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取废物类别信息"""

    def get_treatment_method(
        self,
        method_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取处理方法信息"""

    def get_suitable_treatments(
        self,
        waste_type: str
    ) -> List[str]:
        """获取适合的处理方式"""

    def search_by_keyword(
        self,
        keyword: str,
        search_in: str = 'all'
    ) -> Dict[str, Any]:
        """关键词搜索"""

    def compare_treatments(
        self,
        waste_type: str
    ) -> Dict[str, Any]:
        """比较处理方式"""

    def get_waste_hierarchy(self) -> Dict[str, Any]:
        """获取废物层级信息"""
```

**废物类别 ID:**
- `municipal_solid_waste`: 城市固体废物
- `industrial_waste`: 工业废物
- `construction_waste`: 建筑垃圾
- `agricultural_waste`: 农业废物

**处理方法 ID:**
- `landfill`: 填埋
- `incineration`: 焚烧
- `composting`: 堆肥
- `anaerobic_digestion`: 厌氧消化
- `recycling`: 回收
- `pyrolysis`: 热解

### TerminologyDB

```python
class TerminologyDB:
    """术语数据库"""

    def __init__(self, data_dir: Optional[Path] = None):
        """初始化术语库"""

    def get_term(self, term_id: str) -> Optional[Dict[str, Any]]:
        """获取术语信息"""

    def translate(
        self,
        term: str,
        to_language: str = 'zh'
    ) -> Optional[str]:
        """翻译术语"""

    def expand_abbreviation(
        self,
        abbr: str,
        language: str = 'zh'
    ) -> Optional[str]:
        """展开缩写"""

    def explain_term(
        self,
        term: str,
        detailed: bool = True
    ) -> str:
        """解释术语"""

    def search_terms(
        self,
        keyword: str,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """搜索术语"""

    def list_categories(self) -> List[str]:
        """列出所有类别"""
```

**术语类别:**
- `waste_types`: 废物类型
- `treatment`: 处理技术
- `environmental`: 环境影响
- `management`: 废物管理
- `circular_economy`: 循环经济
- `standards`: 标准规范

### StandardsDB

```python
class StandardsDB:
    """标准规范数据库"""

    def __init__(self, data_dir: Optional[Path] = None):
        """初始化标准库"""

    def get_standard(
        self,
        standard_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取标准信息"""

    def get_policy(
        self,
        policy_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取政策信息"""

    def get_best_practice(
        self,
        practice_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取最佳实践"""

    def search_standards(
        self,
        keyword: str,
        standard_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """搜索标准"""

    def get_compliance_requirements(
        self,
        region: str,
        waste_type: str
    ) -> Dict[str, Any]:
        """获取合规要求"""
```

### DomainPrompts

```python
class DomainPrompts:
    """领域提示词"""

    @classmethod
    def get_system_prompt(
        cls,
        prompt_type: PromptType
    ) -> str:
        """获取系统提示词"""

    @classmethod
    def create_emission_calculation_prompt(
        cls,
        waste_type: str,
        treatment_method: str,
        quantity: float,
        additional_context: Optional[str] = None
    ) -> Dict[str, str]:
        """创建排放计算提示词"""

    @classmethod
    def create_treatment_recommendation_prompt(
        cls,
        waste_type: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """创建处理建议提示词"""
```

**提示词类型 (PromptType):**
- `GENERAL_CONSULTATION`: 通用咨询
- `EMISSION_CALCULATION`: 排放计算
- `TREATMENT_RECOMMENDATION`: 处理建议
- `LCA_ANALYSIS`: LCA 分析
- `POLICY_COMPLIANCE`: 政策合规
- `RESEARCH_SUPPORT`: 科研支持
- `REPORT_GENERATION`: 报告生成
- `DATA_ANALYSIS`: 数据分析

---

## 工作流系统

### WorkflowContext

```python
class WorkflowContext:
    """工作流上下文"""

    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        """初始化上下文"""

    def set(self, key: str, value: Any):
        """设置数据"""

    def get(self, key: str, default: Any = None) -> Any:
        """获取数据"""

    def has(self, key: str) -> bool:
        """检查键是否存在"""

    def update(self, data: Dict[str, Any]):
        """批量更新"""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
```

### WorkflowStep

```python
@dataclass
class WorkflowStep:
    """工作流步骤"""
    name: str                                # 步骤名称
    description: str                         # 步骤描述
    execute_func: Callable                   # 执行函数
    required_inputs: List[str]               # 必需输入
    optional_inputs: List[str]               # 可选输入
    outputs: List[str]                       # 输出
    status: StepStatus                       # 状态
    max_retries: int = 3                    # 最大重试次数
    retry_delay: float = 1.0                # 重试延迟
```

### WorkflowResult

```python
@dataclass
class WorkflowResult:
    """工作流结果"""
    success: bool                            # 是否成功
    total_steps: int                         # 总步骤数
    completed_steps: int                     # 完成步骤数
    step_results: List[Dict[str, Any]]       # 步骤结果
    context: WorkflowContext                 # 最终上下文
    duration: float                          # 执行时长
    error: Optional[str] = None              # 错误信息

    @property
    def completion_rate(self) -> float:
        """完成率"""
```

### BaseWorkflow

```python
class BaseWorkflow(ABC):
    """工作流基类"""

    def __init__(self, name: str, description: str):
        """初始化工作流"""

    def add_step(
        self,
        name: str,
        description: str,
        execute_func: Callable,
        required_inputs: List[str] = None,
        optional_inputs: List[str] = None,
        outputs: List[str] = None,
        max_retries: int = 3
    ):
        """添加步骤"""

    async def execute(
        self,
        initial_context: Optional[Dict[str, Any]] = None,
        stop_on_error: bool = True
    ) -> WorkflowResult:
        """执行工作流"""

    @abstractmethod
    def _setup_steps(self):
        """设置工作流步骤（子类实现）"""
```

### ResearchWorkflow

```python
class ResearchWorkflow(BaseWorkflow):
    """科研工作流"""

    def __init__(self):
        """初始化科研工作流"""
```

**步骤:**
1. `literature_review` - 文献调研
2. `research_design` - 研究设计
3. `data_collection` - 数据收集
4. `data_analysis` - 数据分析
5. `result_interpretation` - 结果解释
6. `paper_writing` - 论文撰写
7. `conclusion_summary` - 总结

**输入参数:**
- `research_topic` (必需): 研究主题
- `keywords` (可选): 关键词列表
- `methodology_preference` (可选): 方法学偏好

### ReportWorkflow

```python
class ReportWorkflow(BaseWorkflow):
    """报告生成工作流"""

    def __init__(self):
        """初始化报告工作流"""
```

**步骤:**
1. `requirement_analysis` - 需求分析
2. `data_collection` - 数据收集
3. `data_organization` - 数据整理
4. `content_writing` - 内容撰写
5. `chart_creation` - 图表制作
6. `formatting` - 排版格式化
7. `quality_check` - 质量检查

**输入参数:**
- `report_type` (必需): 报告类型
- `report_purpose` (必需): 报告用途
- `target_audience` (可选): 目标受众
- `template` (可选): 模板

### DataAnalysisWorkflow

```python
class DataAnalysisWorkflow(BaseWorkflow):
    """数据分析工作流"""

    def __init__(self):
        """初始化数据分析工作流"""
```

**步骤:**
1. `data_import` - 数据导入
2. `data_exploration` - 数据探索
3. `data_cleaning` - 数据清洗
4. `feature_engineering` - 特征工程
5. `statistical_analysis` - 统计分析
6. `visualization` - 可视化
7. `report_generation` - 生成报告

**输入参数:**
- `data_source` (必需): 数据源
- `file_format` (必需): 文件格式
- `exploration_depth` (可选): 探索深度

### CodingWorkflow

```python
class CodingWorkflow(BaseWorkflow):
    """代码开发工作流"""

    def __init__(self):
        """初始化代码开发工作流"""
```

**步骤:**
1. `requirement_analysis` - 需求分析
2. `design` - 设计方案
3. `implementation` - 编码实现
4. `unit_testing` - 单元测试
5. `code_review` - 代码审查
6. `integration_testing` - 集成测试
7. `documentation` - 文档编写

**输入参数:**
- `feature_request` (必需): 功能需求
- `user_stories` (可选): 用户故事
- `acceptance_criteria` (可选): 验收标准

### WorkflowManager

```python
class WorkflowManager:
    """工作流管理器"""

    def __init__(self):
        """初始化管理器"""

    def register(
        self,
        name: str,
        workflow_class: Type[BaseWorkflow]
    ):
        """注册工作流"""

    def get_workflow(self, name: str) -> Optional[BaseWorkflow]:
        """获取工作流实例"""

    def list_workflows(self) -> List[Dict[str, str]]:
        """列出所有工作流"""

    async def execute_workflow(
        self,
        name: str,
        initial_context: Optional[Dict] = None,
        stop_on_error: bool = True
    ) -> WorkflowResult:
        """执行工作流"""

    def get_workflow_steps(
        self,
        name: str
    ) -> Optional[List[Dict[str, str]]]:
        """获取工作流步骤信息"""

    def get_workflow_by_purpose(
        self,
        purpose: str
    ) -> List[str]:
        """根据用途推荐工作流"""
```

---

## 全局函数

### 获取全局实例

```python
from swagent.tools import get_global_registry
from swagent.domain import (
    get_knowledge_base,
    get_terminology_db,
    get_standards_db
)
from swagent.workflows import get_workflow_manager

# 获取工具注册中心
registry = get_global_registry()

# 获取知识库
kb = get_knowledge_base()
term_db = get_terminology_db()
std_db = get_standards_db()

# 获取工作流管理器
manager = get_workflow_manager()
```

---

## 异常处理

### 自定义异常

```python
# LLM 相关
class LLMError(Exception):
    """LLM 基础异常"""

class LLMConfigError(LLMError):
    """配置错误"""

class LLMAPIError(LLMError):
    """API 调用错误"""

# Agent 相关
class AgentError(Exception):
    """Agent 基础异常"""

class AgentExecutionError(AgentError):
    """执行错误"""

# Tool 相关
class ToolError(Exception):
    """工具基础异常"""

class ToolNotFoundError(ToolError):
    """工具未找到"""

class ToolExecutionError(ToolError):
    """工具执行错误"""

# Workflow 相关
class WorkflowError(Exception):
    """工作流基础异常"""

class WorkflowStepError(WorkflowError):
    """步骤错误"""
```

---

## 类型定义

```python
from typing import (
    Dict, List, Optional, Any, Callable,
    Union, Tuple, AsyncIterator, Awaitable
)
from enum import Enum

class StepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class PromptType(Enum):
    """提示词类型"""
    GENERAL_CONSULTATION = "general_consultation"
    EMISSION_CALCULATION = "emission_calculation"
    TREATMENT_RECOMMENDATION = "treatment_recommendation"
    LCA_ANALYSIS = "lca_analysis"
    POLICY_COMPLIANCE = "policy_compliance"
    RESEARCH_SUPPORT = "research_support"
    REPORT_GENERATION = "report_generation"
    DATA_ANALYSIS = "data_analysis"
```

---

## 版本信息

```python
__version__ = "1.0.0"
__author__ = "SWAgent Team"
__license__ = "MIT"
```

---

## 更多信息

完整使用示例请参考:
- [用户指南](user_guide.md)
- [架构设计](architecture.md)
- [开发指南](development.md)
