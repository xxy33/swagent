"""
配置管理模块
负责读取和管理项目配置
"""
import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv
import re


class Config:
    """配置管理类"""

    _instance: Optional['Config'] = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化配置"""
        if not self._config:
            self._load_config()

    def _load_config(self):
        """加载配置文件"""
        # 加载环境变量
        load_dotenv()

        # 查找config.yaml文件
        config_path = self._find_config_file()

        if config_path and config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}

            # 替换环境变量
            self._config = self._replace_env_vars(self._config)
        else:
            # 使用默认配置
            self._config = self._get_default_config()

    def _find_config_file(self) -> Optional[Path]:
        """查找配置文件"""
        # 当前工作目录
        current_dir = Path.cwd()
        config_file = current_dir / 'config.yaml'
        if config_file.exists():
            return config_file

        # 项目根目录（向上查找）
        for parent in current_dir.parents:
            config_file = parent / 'config.yaml'
            if config_file.exists():
                return config_file

        # 脚本所在目录
        script_dir = Path(__file__).parent.parent.parent
        config_file = script_dir / 'config.yaml'
        if config_file.exists():
            return config_file

        return None

    def _replace_env_vars(self, config: Any) -> Any:
        """递归替换配置中的环境变量"""
        if isinstance(config, dict):
            return {k: self._replace_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._replace_env_vars(item) for item in config]
        elif isinstance(config, str):
            # 匹配 ${VAR_NAME} 格式
            pattern = r'\$\{([^}]+)\}'
            matches = re.findall(pattern, config)
            for var_name in matches:
                env_value = os.getenv(var_name, '')
                config = config.replace(f'${{{var_name}}}', env_value)
            return config
        else:
            return config

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'app': {
                'name': 'SolidWaste-Agent',
                'version': '0.1.0',
                'debug': False
            },
            'llm': {
                'default_provider': 'openai',
                'providers': {
                    'openai': {
                        'api_key': os.getenv('OPENAI_API_KEY', ''),
                        'base_url': 'https://api.openai.com/v1',
                        'default_model': 'gpt-4',
                        'timeout': 60,
                        'max_retries': 3
                    }
                }
            },
            'logging': {
                'level': 'INFO',
                'console': {'enabled': True}
            }
        }

    def get(self, path: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            path: 配置路径，使用.分隔，如 'llm.default_provider'
            default: 默认值

        Returns:
            配置值
        """
        keys = path.split('.')
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, path: str, value: Any):
        """
        设置配置值

        Args:
            path: 配置路径，使用.分隔
            value: 要设置的值
        """
        keys = path.split('.')
        config = self._config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def get_llm_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        获取LLM配置

        Args:
            provider: 提供商名称，None表示使用默认

        Returns:
            LLM配置字典
        """
        if provider is None:
            provider = self.get('llm.default_provider', 'openai')

        return self.get(f'llm.providers.{provider}', {})

    def reload(self):
        """重新加载配置"""
        self._config = {}
        self._load_config()

    @property
    def all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()


# 全局配置实例
_global_config: Optional[Config] = None


def get_config() -> Config:
    """获取全局配置实例"""
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config
