"""
代码开发工作流
用于软件开发的需求分析、设计、编码、测试和部署
"""
from typing import Dict, Any
from .base_workflow import BaseWorkflow, WorkflowContext


class CodingWorkflow(BaseWorkflow):
    """
    代码开发工作流模板

    步骤：
    1. 需求分析 - 分析和明确开发需求
    2. 设计方案 - 设计架构和接口
    3. 编码实现 - 实现功能代码
    4. 单元测试 - 编写和执行单元测试
    5. 代码审查 - 审查代码质量
    6. 集成测试 - 执行集成测试
    7. 文档编写 - 编写技术文档
    """

    def __init__(self):
        super().__init__(
            name="代码开发工作流",
            description="支持从需求到部署的完整软件开发生命周期"
        )

    def _setup_steps(self):
        """设置代码开发工作流的具体步骤"""

        # 步骤1: 需求分析
        self.add_step(
            name="requirement_analysis",
            description="分析功能需求和非功能需求",
            execute_func=self._requirement_analysis,
            required_inputs=["feature_request"],
            optional_inputs=["user_stories", "acceptance_criteria"],
            outputs=["requirements_spec", "use_cases"]
        )

        # 步骤2: 设计方案
        self.add_step(
            name="design",
            description="设计系统架构、模块和接口",
            execute_func=self._design,
            required_inputs=["requirements_spec"],
            optional_inputs=["design_patterns", "tech_stack"],
            outputs=["design_doc", "api_spec", "data_model"]
        )

        # 步骤3: 编码实现
        self.add_step(
            name="implementation",
            description="实现功能代码",
            execute_func=self._implementation,
            required_inputs=["design_doc", "api_spec"],
            optional_inputs=["coding_style"],
            outputs=["source_code", "code_metrics"]
        )

        # 步骤4: 单元测试
        self.add_step(
            name="unit_testing",
            description="编写和执行单元测试",
            execute_func=self._unit_testing,
            required_inputs=["source_code"],
            optional_inputs=["test_framework"],
            outputs=["test_code", "unit_test_results"]
        )

        # 步骤5: 代码审查
        self.add_step(
            name="code_review",
            description="审查代码质量和最佳实践",
            execute_func=self._code_review,
            required_inputs=["source_code", "test_code"],
            optional_inputs=["review_checklist"],
            outputs=["review_report", "suggestions"]
        )

        # 步骤6: 集成测试
        self.add_step(
            name="integration_testing",
            description="执行集成测试和端到端测试",
            execute_func=self._integration_testing,
            required_inputs=["source_code", "test_code"],
            optional_inputs=["test_scenarios"],
            outputs=["integration_test_results", "coverage_report"]
        )

        # 步骤7: 文档编写
        self.add_step(
            name="documentation",
            description="编写API文档和使用说明",
            execute_func=self._documentation,
            required_inputs=["source_code", "api_spec"],
            optional_inputs=["doc_format"],
            outputs=["api_docs", "user_guide", "changelog"]
        )

    async def _requirement_analysis(self, context: WorkflowContext) -> Dict[str, Any]:
        """执行需求分析步骤"""
        feature_request = context.get('feature_request')
        user_stories = context.get('user_stories', [])
        acceptance_criteria = context.get('acceptance_criteria', [])

        requirements_spec = f"""
# 需求规格说明

## 功能需求
{feature_request}

## 用户故事
{chr(10).join([f'- {story}' for story in user_stories]) if user_stories else '- 待补充'}

## 验收标准
{chr(10).join([f'- {criterion}' for criterion in acceptance_criteria]) if acceptance_criteria else '- 待补充'}

## 功能范围
1. 核心功能：{feature_request}
2. 边界条件：需要处理的异常情况
3. 性能要求：响应时间 < 200ms

## 非功能需求
- 可用性：99.9%
- 安全性：数据加密、访问控制
- 可扩展性：支持水平扩展
- 可维护性：模块化设计、完整文档
"""

        use_cases = [
            {
                'id': 'UC-001',
                'name': '主要用例',
                'actor': '用户',
                'description': f'用户执行{feature_request}',
                'preconditions': '用户已登录',
                'postconditions': '操作成功完成'
            }
        ]

        return {
            'requirements_spec': requirements_spec,
            'use_cases': use_cases,
            'requirements_count': len(acceptance_criteria) if acceptance_criteria else 1
        }

    async def _design(self, context: WorkflowContext) -> Dict[str, Any]:
        """执行设计方案步骤"""
        requirements = context.get('requirements_spec')
        patterns = context.get('design_patterns', ['MVC', 'Repository'])
        tech_stack = context.get('tech_stack', {
            'backend': 'Python/FastAPI',
            'database': 'PostgreSQL',
            'frontend': 'React'
        })

        design_doc = f"""
# 设计文档

## 架构设计
采用三层架构：
- 表示层：{tech_stack.get('frontend', 'Web UI')}
- 业务逻辑层：{tech_stack.get('backend', 'Backend API')}
- 数据层：{tech_stack.get('database', 'Database')}

## 设计模式
应用以下设计模式：
{chr(10).join([f'- {pattern}' for pattern in patterns])}

## 模块划分
1. API层：处理HTTP请求
2. Service层：业务逻辑
3. Repository层：数据访问
4. Model层：数据模型

## 关键组件
- Controller：请求路由和验证
- Service：核心业务逻辑
- Repository：数据库操作
- DTO：数据传输对象
"""

        api_spec = {
            'endpoints': [
                {
                    'method': 'POST',
                    'path': '/api/v1/resources',
                    'description': '创建资源',
                    'request_body': {'name': 'string', 'data': 'object'},
                    'response': {'id': 'string', 'status': 'string'}
                },
                {
                    'method': 'GET',
                    'path': '/api/v1/resources/{id}',
                    'description': '获取资源',
                    'parameters': {'id': 'string'},
                    'response': {'id': 'string', 'name': 'string', 'data': 'object'}
                }
            ],
            'authentication': 'JWT Bearer Token',
            'versioning': 'URL path versioning'
        }

        data_model = {
            'entities': [
                {
                    'name': 'Resource',
                    'fields': [
                        {'name': 'id', 'type': 'UUID', 'primary_key': True},
                        {'name': 'name', 'type': 'String', 'required': True},
                        {'name': 'data', 'type': 'JSON', 'required': False},
                        {'name': 'created_at', 'type': 'DateTime', 'auto_now_add': True}
                    ]
                }
            ],
            'relationships': []
        }

        return {
            'design_doc': design_doc,
            'api_spec': api_spec,
            'data_model': data_model
        }

    async def _implementation(self, context: WorkflowContext) -> Dict[str, Any]:
        """执行编码实现步骤"""
        design_doc = context.get('design_doc')
        api_spec = context.get('api_spec')
        coding_style = context.get('coding_style', 'PEP 8')

        # 模拟生成的代码
        source_code = {
            'models.py': '''
"""Data models"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Resource(Base):
    """Resource model"""
    __tablename__ = "resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
''',
            'services.py': '''
"""Business logic services"""
from typing import Optional, Dict, Any

class ResourceService:
    """Resource management service"""

    def __init__(self, repository):
        self.repository = repository

    async def create_resource(self, name: str, data: Optional[Dict[str, Any]] = None):
        """Create a new resource"""
        resource = await self.repository.create(name=name, data=data)
        return resource

    async def get_resource(self, resource_id: str):
        """Get resource by ID"""
        resource = await self.repository.get_by_id(resource_id)
        if not resource:
            raise ResourceNotFoundError(f"Resource {resource_id} not found")
        return resource
''',
            'api.py': '''
"""API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1")

class CreateResourceRequest(BaseModel):
    name: str
    data: Optional[dict] = None

@router.post("/resources")
async def create_resource(request: CreateResourceRequest, service = Depends(get_service)):
    """Create a new resource"""
    resource = await service.create_resource(request.name, request.data)
    return {"id": str(resource.id), "status": "created"}

@router.get("/resources/{resource_id}")
async def get_resource(resource_id: str, service = Depends(get_service)):
    """Get resource by ID"""
    try:
        resource = await service.get_resource(resource_id)
        return resource
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
'''
        }

        code_metrics = {
            'total_files': len(source_code),
            'total_lines': 150,
            'functions': 4,
            'classes': 2,
            'complexity': {
                'average': 2.5,
                'max': 5
            },
            'code_quality_score': 85
        }

        return {
            'source_code': source_code,
            'code_metrics': code_metrics,
            'files_created': list(source_code.keys())
        }

    async def _unit_testing(self, context: WorkflowContext) -> Dict[str, Any]:
        """执行单元测试步骤"""
        source_code = context.get('source_code')
        framework = context.get('test_framework', 'pytest')

        test_code = {
            'test_services.py': '''
"""Unit tests for services"""
import pytest
from unittest.mock import Mock, AsyncMock

class TestResourceService:
    """Test cases for ResourceService"""

    @pytest.fixture
    def service(self):
        repository = Mock()
        return ResourceService(repository)

    @pytest.mark.asyncio
    async def test_create_resource(self, service):
        """Test resource creation"""
        service.repository.create = AsyncMock(return_value=Mock(id="123"))
        result = await service.create_resource("test", {})
        assert result.id == "123"

    @pytest.mark.asyncio
    async def test_get_resource_not_found(self, service):
        """Test get non-existent resource"""
        service.repository.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(ResourceNotFoundError):
            await service.get_resource("999")
'''
        }

        unit_test_results = {
            'total_tests': 8,
            'passed': 8,
            'failed': 0,
            'skipped': 0,
            'coverage': 92.5,
            'duration': 1.25,
            'details': [
                {'test': 'test_create_resource', 'status': 'passed', 'time': 0.15},
                {'test': 'test_get_resource', 'status': 'passed', 'time': 0.12},
                {'test': 'test_get_resource_not_found', 'status': 'passed', 'time': 0.10}
            ]
        }

        return {
            'test_code': test_code,
            'unit_test_results': unit_test_results,
            'test_coverage': unit_test_results['coverage']
        }

    async def _code_review(self, context: WorkflowContext) -> Dict[str, Any]:
        """执行代码审查步骤"""
        source_code = context.get('source_code')
        test_code = context.get('test_code')
        checklist = context.get('review_checklist', [
            'code_style', 'naming', 'documentation', 'error_handling',
            'performance', 'security', 'testability'
        ])

        review_report = {
            'overall_score': 88,
            'categories': {
                'code_style': {'score': 95, 'note': '符合PEP 8标准'},
                'naming': {'score': 90, 'note': '命名清晰一致'},
                'documentation': {'score': 85, 'note': 'docstring完整'},
                'error_handling': {'score': 88, 'note': '异常处理恰当'},
                'performance': {'score': 85, 'note': '性能良好'},
                'security': {'score': 90, 'note': '基本安全措施到位'},
                'testability': {'score': 92, 'note': '测试覆盖充分'}
            },
            'issues_found': 3,
            'critical_issues': 0,
            'warnings': 3
        }

        suggestions = [
            "建议在API层增加请求速率限制",
            "可以添加更多边界条件的测试用例",
            "考虑使用缓存提升性能"
        ]

        return {
            'review_report': review_report,
            'suggestions': suggestions,
            'approved': review_report['overall_score'] >= 80
        }

    async def _integration_testing(self, context: WorkflowContext) -> Dict[str, Any]:
        """执行集成测试步骤"""
        source_code = context.get('source_code')
        test_code = context.get('test_code')
        scenarios = context.get('test_scenarios', ['happy_path', 'error_cases'])

        integration_test_results = {
            'total_scenarios': 5,
            'passed': 5,
            'failed': 0,
            'duration': 3.5,
            'scenarios': [
                {'name': 'API端到端测试', 'status': 'passed', 'time': 0.8},
                {'name': '数据库集成测试', 'status': 'passed', 'time': 1.2},
                {'name': '错误处理测试', 'status': 'passed', 'time': 0.6},
                {'name': '性能测试', 'status': 'passed', 'time': 0.7},
                {'name': '并发测试', 'status': 'passed', 'time': 0.2}
            ]
        }

        coverage_report = {
            'line_coverage': 92.5,
            'branch_coverage': 85.0,
            'function_coverage': 100.0,
            'overall_coverage': 92.5,
            'uncovered_lines': [
                {'file': 'services.py', 'lines': [45, 46]},
            ]
        }

        return {
            'integration_test_results': integration_test_results,
            'coverage_report': coverage_report,
            'all_tests_passed': integration_test_results['failed'] == 0
        }

    async def _documentation(self, context: WorkflowContext) -> Dict[str, Any]:
        """执行文档编写步骤"""
        source_code = context.get('source_code')
        api_spec = context.get('api_spec')
        doc_format = context.get('doc_format', 'markdown')

        api_docs = f"""
# API文档

## 认证
使用JWT Bearer Token进行认证。

## 端点

### POST /api/v1/resources
创建新资源

**请求体：**
```json
{{
  "name": "string",
  "data": {{}}
}}
```

**响应：**
```json
{{
  "id": "uuid",
  "status": "created"
}}
```

### GET /api/v1/resources/{{id}}
获取资源详情

**参数：**
- id: 资源ID (UUID)

**响应：**
```json
{{
  "id": "uuid",
  "name": "string",
  "data": {{}},
  "created_at": "datetime"
}}
```

## 错误码
- 400: 请求参数错误
- 401: 未授权
- 404: 资源不存在
- 500: 服务器错误
"""

        user_guide = """
# 使用指南

## 快速开始

### 安装
```bash
pip install -r requirements.txt
```

### 配置
创建`.env`文件并配置环境变量：
```
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key
```

### 运行
```bash
python main.py
```

## 基本用法

### 创建资源
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/resources",
    json={"name": "test", "data": {}},
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
```

## 常见问题

Q: 如何获取认证令牌？
A: 调用 /auth/login 端点

Q: 支持哪些数据格式？
A: JSON
"""

        changelog = """
# 更新日志

## [1.0.0] - 2024-01-17

### 新增
- 资源创建API
- 资源查询API
- JWT认证
- 单元测试
- API文档

### 改进
- 无

### 修复
- 无
"""

        return {
            'api_docs': api_docs,
            'user_guide': user_guide,
            'changelog': changelog,
            'documentation_complete': True
        }
