import os
import time
import logging
from flask import Flask, request, g
from flask_cors import CORS
from flask import has_request_context
from flask.logging import default_handler
from routes import register_routes
# 导入配置模块
from config import config
# 导入数据库操作模块
from db_orm import (
    init_db
)
app = Flask(__name__)
CORS(app)  # 启用跨域请求支持

# 配置 JSON 编码以支持中文字符
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

register_routes(app)

if __name__ == '__main__':
    # 打印配置信息
    print(f"配置加载完成:")
    print(f"  数据库路径: {config.db_path}")
    print(f"  LDAP服务器: {config.ldap_config.get('server', 'N/A')}")
    print(f"  LDAP端口: {config.ldap_config.get('port', 'N/A')}")
    
    # 初始化数据库
    init_db()
    
    # 启动Flask应用
    app.run(debug=True, host="0.0.0.0", port=5000)