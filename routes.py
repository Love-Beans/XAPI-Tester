# routes.py
from flask import Flask
from api_view import view_bp
from api_routes import register_api_routes
from api.api_advanced_config import advanced_config_bp

def register_routes(app: Flask):
    """
    注册所有路由
    """
    # 注册视图蓝图
    app.register_blueprint(view_bp)
    
    # 注册高级配置API蓝图
    app.register_blueprint(advanced_config_bp)
    
    # 注册API路由
    register_api_routes(app)