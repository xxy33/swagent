"""
消息系统定义
用于Agent之间的通信
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime
import uuid
import json


class MessageType(Enum):
    """消息类型"""
    # 基础类型
    REQUEST = "request"         # 请求
    RESPONSE = "response"       # 响应
    
    # 任务类型
    TASK = "task"               # 任务分配
    TASK_RESULT = "task_result" # 任务结果
    
    # 协作类型
    QUERY = "query"             # 查询
    INFORM = "inform"           # 通知
    CONFIRM = "confirm"         # 确认
    REJECT = "reject"           # 拒绝
    
    # 系统类型
    SYSTEM = "system"           # 系统消息
    ERROR = "error"             # 错误消息
    HEARTBEAT = "heartbeat"     # 心跳


class ContentType(Enum):
    """内容类型"""
    TEXT = "text"               # 纯文本
    CODE = "code"               # 代码
    JSON = "json"               # JSON数据
    MARKDOWN = "markdown"       # Markdown
    FILE = "file"               # 文件引用
    IMAGE = "image"             # 图片
    TABLE = "table"             # 表格数据


@dataclass
class MessageContent:
    """消息内容"""
    type: ContentType
    data: Any
    language: Optional[str] = None  # 代码语言
    filename: Optional[str] = None  # 文件名
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type.value,
            "data": self.data,
            "language": self.language,
            "filename": self.filename
        }


@dataclass
class Message:
    """
    消息类
    
    Agent之间通信的基本单元
    """
    sender: str                          # 发送者ID
    content: str                         # 消息内容
    msg_type: MessageType = MessageType.REQUEST
    sender_name: str = ""                # 发送者名称
    receiver: Optional[str] = None       # 接收者ID (None表示广播)
    receiver_name: Optional[str] = None  # 接收者名称
    
    # 元数据
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    parent_id: Optional[str] = None      # 父消息ID (用于追踪对话)
    thread_id: Optional[str] = None      # 线程ID (用于分组)
    
    # 扩展内容
    attachments: List[MessageContent] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 优先级和标签
    priority: int = 0                    # 优先级 (0最低)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "sender": self.sender,
            "sender_name": self.sender_name,
            "receiver": self.receiver,
            "receiver_name": self.receiver_name,
            "content": self.content,
            "msg_type": self.msg_type.value,
            "timestamp": self.timestamp.isoformat(),
            "parent_id": self.parent_id,
            "thread_id": self.thread_id,
            "attachments": [a.to_dict() for a in self.attachments],
            "metadata": self.metadata,
            "priority": self.priority,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """从字典创建"""
        data['msg_type'] = MessageType(data['msg_type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['attachments'] = [
            MessageContent(
                type=ContentType(a['type']),
                data=a['data'],
                language=a.get('language'),
                filename=a.get('filename')
            ) for a in data.get('attachments', [])
        ]
        return cls(**data)
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    def reply(self, content: str, msg_type: MessageType = MessageType.RESPONSE) -> 'Message':
        """创建回复消息"""
        return Message(
            sender=self.receiver or "",
            sender_name=self.receiver_name or "",
            receiver=self.sender,
            receiver_name=self.sender_name,
            content=content,
            msg_type=msg_type,
            parent_id=self.id,
            thread_id=self.thread_id or self.id
        )


@dataclass
class ThinkResult:
    """思考结果"""
    action: str                          # 要执行的动作
    reasoning: str                       # 推理过程
    plan: List[str] = field(default_factory=list)  # 执行计划
    tools_needed: List[str] = field(default_factory=list)  # 需要的工具
    confidence: float = 0.0              # 置信度
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionResult:
    """行动结果"""
    success: bool                        # 是否成功
    content: str                         # 结果内容
    artifacts: List[MessageContent] = field(default_factory=list)  # 产出物
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None          # 错误信息
