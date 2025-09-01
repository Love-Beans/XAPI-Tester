# api_routes.py
from flask import Flask
from auth import require_auth

def register_api_routes(app: Flask):
    """
    注册所有API路由
    """
    from api.api_server import (
        send_request, save_request_info, get_request_info, get_request_history,copy_request, delete_request   )
    from api.api_user import (
        register, login, get_user_info,
        get_all_users, verify_token_api
    )
    from api.api_project import (
        get_projects, create_new_project, get_project_detail,
        get_project_request_list,
        get_project_members_list, add_project_member, remove_project_member_api
    )
    from api.api_project_env import (
        get_env, save_env, delete_env
    )
    
    # 注册API路由
    app.add_url_rule('/api/send-request', 'send_request', require_auth(send_request), methods=['POST'])
    app.add_url_rule('/api/save-request-info', 'save_request_info', require_auth(save_request_info), methods=['POST'])
    app.add_url_rule('/api/copy_request_info', 'copy_request', require_auth(copy_request), methods=['POST'])
    app.add_url_rule('/api/delete_request_info', 'delete_request', require_auth(delete_request), methods=['POST'])
    # 项目相关
    app.add_url_rule('/api/request-info', 'get_request_info', require_auth(get_request_info), methods=['GET'])
    app.add_url_rule('/api/history/<int:request_info_id>', 'get_request_history', require_auth(get_request_history), methods=['GET'])
    app.add_url_rule('/api/register', 'register', register, methods=['POST'])
    app.add_url_rule('/api/login', 'login', login, methods=['POST'])
    app.add_url_rule('/api/verify_token', 'verify_token_api', verify_token_api, methods=['GET'])
    app.add_url_rule('/api/user/<int:user_id>', 'get_user_info', get_user_info, methods=['GET'])
    app.add_url_rule('/api/admin/users', 'get_all_users', require_auth(get_all_users), methods=['GET'])
    app.add_url_rule('/api/users', 'get_users', require_auth(get_all_users), methods=['GET'])
    # 以下路由已删除，因为 UserRequestRelation 表已移除：
    # - /api/user-requests
    # - /api/user-request-relation
    # - /api/admin/requests
    # - /api/admin/assign-request
    # - /api/admin/unassign-request
    
    # 项目管理相关路由
    app.add_url_rule('/api/projects', 'get_projects', require_auth(get_projects), methods=['GET'])
    app.add_url_rule('/api/projects', 'create_new_project', require_auth(create_new_project), methods=['POST'])
    app.add_url_rule('/api/projects/<int:project_id>', 'get_project_detail', require_auth(get_project_detail), methods=['GET'])
    app.add_url_rule('/api/projects/<int:project_id>/requests', 'get_project_request_list', require_auth(get_project_request_list), methods=['GET'])
    app.add_url_rule('/api/projects/members', 'get_project_members_list', require_auth(get_project_members_list), methods=['GET'])
    app.add_url_rule('/api/projects/members', 'add_project_member', require_auth(add_project_member), methods=['POST'])
    app.add_url_rule('/api/projects/members', 'remove_project_member_api', require_auth(remove_project_member_api), methods=['DELETE'])

    # 项目配置路由
    app.add_url_rule('/api/project_env/<int:project_id>', 'get_env', require_auth(get_env), methods=['GET'])
    app.add_url_rule('/api/project_env/<int:project_id>', 'save_env', require_auth(save_env), methods=['POST'])
    app.add_url_rule('/api/project_env/<int:project_id>', 'delete_env', require_auth(delete_env), methods=['DELETE'])
