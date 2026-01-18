"""
固废领域标准规范库
提供标准、法规、指南的查询功能
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class StandardsDB:
    """标准规范数据库"""

    def __init__(self, data_path: Optional[Path] = None):
        """
        初始化标准库

        Args:
            data_path: 数据文件路径，默认为模块内置路径
        """
        if data_path is None:
            data_path = Path(__file__).parent / "data" / "standards.json"

        self.data_path = Path(data_path)
        self._standards_data = None
        self._load_data()

    def _load_data(self):
        """加载标准数据"""
        if self.data_path.exists():
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self._standards_data = json.load(f)

    def get_standard(self, standard_id: str, region: str = 'china') -> Optional[Dict[str, Any]]:
        """
        获取标准信息

        Args:
            standard_id: 标准编号，如 'GB18485-2014'
            region: 区域 ('china' 或 'international')

        Returns:
            标准信息字典
        """
        if not self._standards_data:
            return None

        standards = self._standards_data.get('standards', {})

        if region == 'china':
            china_standards = standards.get('china_national_standards', {})
            return china_standards.get(standard_id)
        elif region == 'international':
            intl_standards = standards.get('international_standards', {})
            return intl_standards.get(standard_id)

        # 如果没有指定区域，搜索所有区域
        for region_data in standards.values():
            if isinstance(region_data, dict) and standard_id in region_data:
                return region_data[standard_id]

        return None

    def get_regulation(self, regulation_id: str, level: str = 'national') -> Optional[Dict[str, Any]]:
        """
        获取法规信息

        Args:
            regulation_id: 法规标识
            level: 层级 ('national' 或 'local')

        Returns:
            法规信息字典
        """
        if not self._standards_data:
            return None

        regulations = self._standards_data.get('regulations', {})

        if level == 'national':
            laws = regulations.get('china_laws', {})
            return laws.get(regulation_id)
        elif level == 'local':
            local_regs = regulations.get('local_regulations', {})
            return local_regs.get(regulation_id)

        return None

    def search_standards(
        self,
        keyword: str,
        category: Optional[str] = None,
        region: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索标准

        Args:
            keyword: 搜索关键词
            category: 标准类别，如 'emission_standard', 'technical_specification'
            region: 区域限定

        Returns:
            匹配的标准列表
        """
        if not self._standards_data:
            return []

        results = []
        standards = self._standards_data.get('standards', {})
        keyword_lower = keyword.lower()

        # 确定搜索范围
        search_regions = {}
        if region:
            if region == 'china':
                search_regions['china'] = standards.get('china_national_standards', {})
            elif region == 'international':
                search_regions['international'] = standards.get('international_standards', {})
        else:
            search_regions['china'] = standards.get('china_national_standards', {})
            search_regions['international'] = standards.get('international_standards', {})
            search_regions['technical'] = standards.get('technical_guidelines', {})
            search_regions['industry'] = standards.get('industry_standards', {})

        # 搜索
        for region_name, region_data in search_regions.items():
            if not isinstance(region_data, dict):
                continue

            for std_id, std_data in region_data.items():
                if not isinstance(std_data, dict):
                    continue

                # 类别过滤
                if category and std_data.get('category') != category:
                    continue

                # 关键词匹配
                if self._match_standard(std_id, std_data, keyword_lower):
                    results.append({
                        'id': std_id,
                        'region': region_name,
                        'data': std_data
                    })

        return results

    def _match_standard(self, std_id: str, std_data: Dict[str, Any], keyword: str) -> bool:
        """
        检查标准是否匹配关键词

        Args:
            std_id: 标准ID
            std_data: 标准数据
            keyword: 关键词（小写）

        Returns:
            是否匹配
        """
        # 检查标准ID
        if keyword in std_id.lower():
            return True

        # 检查名称
        full_name = std_data.get('full_name', '')
        full_name_en = std_data.get('full_name_en', '')

        if keyword in full_name.lower() or keyword in full_name_en.lower():
            return True

        # 检查范围
        scope = std_data.get('scope', '')
        if isinstance(scope, str) and keyword in scope.lower():
            return True

        return False

    def get_emission_standards(self, waste_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取排放标准

        Args:
            waste_type: 废物类型过滤

        Returns:
            排放标准列表
        """
        return self.search_standards('', category='emission_standard')

    def get_china_standards(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        获取中国国家标准

        Args:
            category: 类别过滤

        Returns:
            标准字典
        """
        if not self._standards_data:
            return {}

        standards = self._standards_data.get('standards', {}).get('china_national_standards', {})

        if category:
            return {k: v for k, v in standards.items() if v.get('category') == category}

        return standards

    def get_international_standards(self, organization: Optional[str] = None) -> Dict[str, Any]:
        """
        获取国际标准

        Args:
            organization: 组织过滤，如 'ISO', 'European Union'

        Returns:
            标准字典
        """
        if not self._standards_data:
            return {}

        standards = self._standards_data.get('standards', {}).get('international_standards', {})

        if organization:
            return {
                k: v for k, v in standards.items()
                if v.get('organization') == organization
            }

        return standards

    def get_ipcc_guidelines(self) -> List[Dict[str, Any]]:
        """
        获取IPCC指南

        Returns:
            IPCC指南列表
        """
        if not self._standards_data:
            return []

        guidelines = self._standards_data.get('standards', {}).get('technical_guidelines', {})

        ipcc_guidelines = []
        for guide_id, guide_data in guidelines.items():
            if 'IPCC' in guide_id:
                ipcc_guidelines.append({
                    'id': guide_id,
                    'data': guide_data
                })

        return ipcc_guidelines

    def get_waste_classification_standards(self) -> List[Dict[str, Any]]:
        """
        获取废物分类标准

        Returns:
            分类标准列表
        """
        return self.search_standards('', category='classification_standard', region='china')

    def get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """
        获取政策信息

        Args:
            policy_id: 政策标识

        Returns:
            政策信息字典
        """
        if not self._standards_data:
            return None

        policies = self._standards_data.get('regulations', {}).get('policies', {})
        return policies.get(policy_id)

    def get_best_practice(self, practice_id: str) -> Optional[Dict[str, Any]]:
        """
        获取最佳实践

        Args:
            practice_id: 实践标识，如 'zero_waste', 'circular_economy'

        Returns:
            最佳实践信息
        """
        if not self._standards_data:
            return None

        practices = self._standards_data.get('best_practices', {})
        return practices.get(practice_id)

    def get_all_best_practices(self) -> Dict[str, Any]:
        """
        获取所有最佳实践

        Returns:
            最佳实践字典
        """
        if not self._standards_data:
            return {}

        return self._standards_data.get('best_practices', {})

    def get_emission_limits(self, standard_id: str) -> Optional[Dict[str, Any]]:
        """
        获取排放限值

        Args:
            standard_id: 标准编号

        Returns:
            排放限值字典
        """
        standard = self.get_standard(standard_id)

        if standard and 'key_requirements' in standard:
            return standard['key_requirements'].get('emission_limits')

        return None

    def compare_standards(self, standard_ids: List[str]) -> Dict[str, Any]:
        """
        比较多个标准

        Args:
            standard_ids: 标准编号列表

        Returns:
            比较结果
        """
        comparison = {
            'standards': {},
            'summary': {}
        }

        for std_id in standard_ids:
            std_data = self.get_standard(std_id)
            if std_data:
                comparison['standards'][std_id] = std_data

        return comparison

    def get_applicable_standards(
        self,
        treatment_method: str,
        region: str = 'china'
    ) -> List[Dict[str, Any]]:
        """
        获取适用于特定处理方法的标准

        Args:
            treatment_method: 处理方法，如 'incineration', 'landfill'
            region: 区域

        Returns:
            适用标准列表
        """
        # 关键词映射
        keyword_map = {
            'incineration': '焚烧',
            'landfill': '填埋',
            'composting': '堆肥',
            'recycling': '回收'
        }

        keyword = keyword_map.get(treatment_method, treatment_method)
        return self.search_standards(keyword, region=region)

    def explain_standard(self, standard_id: str) -> str:
        """
        解释标准（生成人类可读的说明）

        Args:
            standard_id: 标准编号

        Returns:
            解释文本
        """
        standard = self.get_standard(standard_id)

        if not standard:
            return f"未找到标准 '{standard_id}'"

        explanation = []

        # 基本信息
        full_name = standard.get('full_name', standard_id)
        explanation.append(f"{standard_id}: {full_name}")

        # 发布信息
        if 'issue_date' in standard:
            explanation.append(f"发布日期: {standard['issue_date']}")
        if 'effective_date' in standard:
            explanation.append(f"实施日期: {standard['effective_date']}")

        # 适用范围
        if 'scope' in standard:
            explanation.append(f"适用范围: {standard['scope']}")

        # 关键要求
        if 'key_requirements' in standard:
            explanation.append("\n关键要求:")
            reqs = standard['key_requirements']
            if isinstance(reqs, dict):
                for key, value in reqs.items():
                    if isinstance(value, dict):
                        explanation.append(f"  {key}:")
                        for k, v in value.items():
                            explanation.append(f"    - {k}: {v}")
                    else:
                        explanation.append(f"  - {key}: {value}")

        return '\n'.join(explanation)

    def get_all_categories(self) -> Dict[str, List[str]]:
        """
        获取所有类别

        Returns:
            类别字典
        """
        if not self._standards_data:
            return {}

        return self._standards_data.get('categories', {})


# 全局单例
_global_standards_db: Optional[StandardsDB] = None


def get_standards_db() -> StandardsDB:
    """
    获取全局标准库实例

    Returns:
        StandardsDB实例
    """
    global _global_standards_db

    if _global_standards_db is None:
        _global_standards_db = StandardsDB()

    return _global_standards_db
