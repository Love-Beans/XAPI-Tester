# api_view.py
from flask import Blueprint, send_from_directory
import os

# 创建蓝图
view_bp = Blueprint('views', __name__)

@view_bp.route('/')
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'html/project_list.html')

@view_bp.route('/api_tester.html')
def api_tester():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'html/api_tester.html')

@view_bp.route('/login.html')
def login_view():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'html/login.html')

@view_bp.route('/register.html')
def register_view():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'html/register.html')

# admin_requests 页面路由已删除

@view_bp.route('/api_tool_content.html')
def serve_api_tool_content():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'html/api_tool_content.html')

@view_bp.route('/history_content.html')
def serve_history_content():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'html/history_content.html')


@view_bp.route('/project_list.html')
def project_list():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'html/project_list.html')

@view_bp.route('/advanced_config_content.html')
def serve_advanced_config_content():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'html/advanced_config_content.html')

@view_bp.route('/project_config.html')
def serve_project_config():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'html/project_config.html')

@view_bp.route('/js/<path:filename>')
def serve_js_files(filename):
    return send_from_directory(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'js'), filename)