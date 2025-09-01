import re
from ldap3 import Server, Connection, Tls
import ssl
import logging
from typing import Optional, Dict
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('AuthService')
class CachedLDAPAuth:
    def __init__(self, ldap_config: Dict = None):
        # 初始化LDAP配置，如果没有传入则使用配置文件中的配置
        self.ldap_config = ldap_config or config.ldap_config
        self.tls = Tls(validate=ssl.CERT_REQUIRED) if self.ldap_config.get('use_ssl') else None

    def _ldap_auth(self, username: str, password: str) -> bool:
        """执行LDAP认证"""
        try:
            server = Server(
                host=self.ldap_config['server'],
                port=self.ldap_config.get('port', 636),
                use_ssl=self.ldap_config.get('use_ssl', True),
                tls=self.tls
            )

            # 自动发现用户DN
            with Connection(server) as conn:
                if not conn.bind():
                    logger.error(f"匿名绑定失败: {conn.result}")
                    return False

                conn.search(
                    search_base=self.ldap_config['base_dn'],
                    search_filter=f"(&(uid={username})(!(shadowExpire=-1)))"
                    #attributes=['userPrincipalName']
                )

                if not conn.entries:
                    return False

                user_dn = conn.entries[0].entry_dn

            # 验证用户凭证
            with Connection(server, user=user_dn, password=password) as user_conn:
                return user_conn.bind()

        except Exception as e:
            logger.error(f"LDAP错误: {str(e)}")
            return False

    def authenticate(self, username: str,password:str) -> Dict:
        """
        认证入口
        返回: {
            "success": bool,
            "username": str,
            "from_cache": bool
        }
        """
        result = {"success": False, "username": "", "from_cache": False}
        try:
            result["username"] = username
            # LDAP认证
            if self._ldap_auth(username, password):
                result["success"] = True
                logger.info(f"LDAP认证成功: {username}")
            else:
                logger.warning(f"认证失败: {username}")

        except Exception as e:
            logger.error(f"认证异常: {str(e)}")

        return result

# 使用示例
if __name__ == "__main__":
    # 使用配置文件中的配置
    auth = CachedLDAPAuth()
    result = auth.authenticate("test_user", "test_password")
    print(f"""
    认证结果: {result['success']}
    用户名: {result['username']}
    来源: {'缓存' if result['from_cache'] else 'LDAP'}
    """)