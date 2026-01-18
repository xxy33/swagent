"""
固废领域增强模块
提供领域知识库、专业术语、标准规范等支持
"""
from .knowledge_base import KnowledgeBase, get_knowledge_base
from .terminology import TerminologyDB, get_terminology_db
from .standards import StandardsDB, get_standards_db
from .prompts import DomainPrompts, PromptType, get_domain_prompt

__all__ = [
    'KnowledgeBase',
    'get_knowledge_base',
    'TerminologyDB',
    'get_terminology_db',
    'StandardsDB',
    'get_standards_db',
    'DomainPrompts',
    'PromptType',
    'get_domain_prompt',
]
