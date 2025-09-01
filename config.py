import json
import os
from typing import Dict, Any

class Config:
    """配置管理类"""
    
    def __init__(self, config_file: str = None):
        if config_file is None:
            config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        
        self.config_file = config_file
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件未找到: {self.config_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")
    
    def get(self, key: str, default=None):
        """获取配置项"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    @property
    def ldap_config(self) -> Dict[str, Any]:
        """获取LDAP配置"""
        return self.get('ldap_config', {})
    
    @property
    def redis_config(self) -> Dict[str, Any]:
        """获取Redis配置"""
        return self.get('redis_config', {})
    
    @property
    def jwt_config(self) -> Dict[str, Any]:
        """获取JWT配置"""
        return self.get('jwt_config', {})
    
    @property
    def user_config(self) -> Dict[str, Any]:
        """获取用户配置"""
        return self.get('user_config', {})
    
    def is_registration_allowed(self) -> bool:
        """检查是否允许注册"""
        return self.user_config.get('allow_registration', True)
    
    def is_admin_user(self, username: str) -> bool:
        """检查用户是否为管理员"""
        admin_users = self.user_config.get('admin_users', [])
        return username in admin_users
    
    def get_default_role(self) -> str:
        """获取默认用户角色"""
        return self.user_config.get('default_role', 'user')
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return self.get('database', {})
    
    @property
    def db_path(self) -> str:
        """获取数据库路径"""
        db_name = self.get('database.db_path', 'api_tester.db')
        # 如果是相对路径，则相对于项目根目录
        if not os.path.isabs(db_name):
            return os.path.join(os.path.dirname(os.path.abspath(__file__)), db_name)
        return db_name
    
    def reload(self):
        """重新加载配置文件"""
        self._config = self._load_config()

# 全局配置实例
config = Config()

# 为了向后兼容，提供直接访问的变量
LDAP_CONFIG = config.ldap_config
REDIS_CONFIG = config.redis_config
DB_PATH = config.db_path
JWT_SECRET_KEY = config.jwt_config.get('secret_key', 'default-secret-key')