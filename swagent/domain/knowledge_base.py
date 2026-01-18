"""
固废领域知识库
加载和查询废物分类、处理方法等领域知识
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class WasteCategory:
    """废物类别"""
    name_zh: str
    name_en: str
    description: str
    subcategories: Dict[str, Any]


@dataclass
class TreatmentMethod:
    """处理方法"""
    name_zh: str
    name_en: str
    description: str
    types: Dict[str, Any]
    advantages: List[str]
    disadvantages: List[str]
    applicable_waste: List[str]


class KnowledgeBase:
    """固废领域知识库"""

    def __init__(self, data_path: Optional[Path] = None):
        """
        初始化知识库

        Args:
            data_path: 数据文件路径，默认为模块内置路径
        """
        if data_path is None:
            data_path = Path(__file__).parent / "data"

        self.data_path = Path(data_path)
        self._waste_categories = None
        self._treatment_methods = None
        self._emission_factors = None

        # 加载数据
        self._load_data()

    def _load_data(self):
        """加载所有数据文件"""
        # 加载废物分类
        waste_file = self.data_path / "waste_categories.json"
        if waste_file.exists():
            with open(waste_file, 'r', encoding='utf-8') as f:
                self._waste_categories = json.load(f)

        # 加载处理方法
        treatment_file = self.data_path / "treatment_methods.json"
        if treatment_file.exists():
            with open(treatment_file, 'r', encoding='utf-8') as f:
                self._treatment_methods = json.load(f)

    def get_waste_category(self, category_id: str) -> Optional[Dict[str, Any]]:
        """
        获取废物类别信息

        Args:
            category_id: 类别ID，如 'municipal_solid_waste', 'food_waste'

        Returns:
            类别信息字典，不存在则返回None
        """
        if not self._waste_categories:
            return None

        categories = self._waste_categories.get('waste_categories', {})

        # 尝试直接匹配主类别
        if category_id in categories:
            return categories[category_id]

        # 尝试匹配子类别
        for main_cat, main_data in categories.items():
            if 'subcategories' in main_data:
                if category_id in main_data['subcategories']:
                    return main_data['subcategories'][category_id]

        return None

    def get_treatment_method(self, method_id: str) -> Optional[Dict[str, Any]]:
        """
        获取处理方法信息

        Args:
            method_id: 方法ID，如 'landfill', 'incineration', 'composting'

        Returns:
            处理方法信息字典，不存在则返回None
        """
        if not self._treatment_methods:
            return None

        methods = self._treatment_methods.get('treatment_methods', {})
        return methods.get(method_id)

    def get_suitable_treatments(self, waste_type: str) -> List[str]:
        """
        获取适合某类废物的处理方式

        Args:
            waste_type: 废物类型

        Returns:
            适合的处理方式列表
        """
        waste_info = self.get_waste_category(waste_type)

        if waste_info and 'suitable_treatments' in waste_info:
            return waste_info['suitable_treatments']

        # 如果没有直接定义，返回空列表
        return []

    def get_applicable_waste_types(self, treatment_method: str) -> List[str]:
        """
        获取某种处理方法适用的废物类型

        Args:
            treatment_method: 处理方法

        Returns:
            适用的废物类型列表
        """
        method_info = self.get_treatment_method(treatment_method)

        if method_info and 'applicable_waste' in method_info:
            return method_info['applicable_waste']

        return []

    def get_waste_hierarchy(self) -> List[Dict[str, Any]]:
        """
        获取废物管理层级

        Returns:
            废物管理层级列表，按优先级排序
        """
        if not self._treatment_methods:
            return []

        hierarchy = self._treatment_methods.get('waste_hierarchy', {})
        return hierarchy.get('levels', [])

    def search_by_keyword(self, keyword: str, search_in: str = 'all') -> Dict[str, List[Dict[str, Any]]]:
        """
        按关键词搜索知识库

        Args:
            keyword: 搜索关键词
            search_in: 搜索范围 ('waste', 'treatment', 'all')

        Returns:
            搜索结果字典，包含 'waste_categories' 和 'treatment_methods' 两个列表
        """
        results = {
            'waste_categories': [],
            'treatment_methods': []
        }

        keyword_lower = keyword.lower()

        # 搜索废物类别
        if search_in in ['waste', 'all'] and self._waste_categories:
            categories = self._waste_categories.get('waste_categories', {})
            for cat_id, cat_data in categories.items():
                if self._match_keyword(cat_data, keyword_lower):
                    results['waste_categories'].append({
                        'id': cat_id,
                        'data': cat_data
                    })

                # 搜索子类别
                if 'subcategories' in cat_data:
                    for sub_id, sub_data in cat_data['subcategories'].items():
                        if self._match_keyword(sub_data, keyword_lower):
                            results['waste_categories'].append({
                                'id': f"{cat_id}.{sub_id}",
                                'data': sub_data,
                                'parent': cat_id
                            })

        # 搜索处理方法
        if search_in in ['treatment', 'all'] and self._treatment_methods:
            methods = self._treatment_methods.get('treatment_methods', {})
            for method_id, method_data in methods.items():
                if self._match_keyword(method_data, keyword_lower):
                    results['treatment_methods'].append({
                        'id': method_id,
                        'data': method_data
                    })

        return results

    def _match_keyword(self, data: Any, keyword: str) -> bool:
        """
        递归匹配关键词

        Args:
            data: 数据
            keyword: 关键词（小写）

        Returns:
            是否匹配
        """
        if isinstance(data, str):
            return keyword in data.lower()
        elif isinstance(data, dict):
            return any(self._match_keyword(v, keyword) for v in data.values())
        elif isinstance(data, list):
            return any(self._match_keyword(item, keyword) for item in data)
        else:
            return False

    def get_recycling_info(self, material: str) -> Optional[Dict[str, Any]]:
        """
        获取特定材料的回收信息

        Args:
            material: 材料类型，如 'paper', 'plastic', 'metal', 'glass'

        Returns:
            回收信息字典
        """
        recyclables = self.get_waste_category('recyclables')

        if recyclables and 'subcategories' in recyclables:
            return recyclables['subcategories'].get(material)

        return None

    def get_treatment_details(self, method: str, detail_type: Optional[str] = None) -> Dict[str, Any]:
        """
        获取处理方法的详细信息

        Args:
            method: 处理方法
            detail_type: 详细类型，如 'types', 'pollution_control', 'advantages'

        Returns:
            详细信息字典
        """
        method_info = self.get_treatment_method(method)

        if not method_info:
            return {}

        if detail_type:
            return method_info.get(detail_type, {})

        return method_info

    def compare_treatments(self, waste_type: str) -> Dict[str, Any]:
        """
        比较不同处理方式对特定废物的适用性

        Args:
            waste_type: 废物类型

        Returns:
            比较结果字典
        """
        suitable_treatments = self.get_suitable_treatments(waste_type)

        comparison = {
            'waste_type': waste_type,
            'suitable_treatments': suitable_treatments,
            'treatment_details': {}
        }

        for treatment in suitable_treatments:
            method_info = self.get_treatment_method(treatment)
            if method_info:
                comparison['treatment_details'][treatment] = {
                    'name': method_info.get('name_zh', ''),
                    'description': method_info.get('description', ''),
                    'advantages': method_info.get('advantages', []),
                    'disadvantages': method_info.get('disadvantages', [])
                }

        return comparison

    def get_classification_system(self, system_name: str = 'china_4_categories') -> Optional[Dict[str, Any]]:
        """
        获取废物分类系统信息

        Args:
            system_name: 系统名称，默认为中国四分类法

        Returns:
            分类系统信息
        """
        if not self._waste_categories:
            return None

        systems = self._waste_categories.get('classification_systems', {})
        return systems.get(system_name)

    def get_all_waste_categories(self) -> Dict[str, Any]:
        """获取所有废物类别"""
        if not self._waste_categories:
            return {}
        return self._waste_categories.get('waste_categories', {})

    def get_all_treatment_methods(self) -> Dict[str, Any]:
        """获取所有处理方法"""
        if not self._treatment_methods:
            return {}
        return self._treatment_methods.get('treatment_methods', {})


# 全局单例
_global_knowledge_base: Optional[KnowledgeBase] = None


def get_knowledge_base() -> KnowledgeBase:
    """
    获取全局知识库实例

    Returns:
        KnowledgeBase实例
    """
    global _global_knowledge_base

    if _global_knowledge_base is None:
        _global_knowledge_base = KnowledgeBase()

    return _global_knowledge_base
