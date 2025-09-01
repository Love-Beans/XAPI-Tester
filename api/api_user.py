from flask import request, jsonify, g
from auth import generate_token
from config import config
from db_orm import (
    create_user,
    verify_user,
    get_user_by_id,
    get_user_by_username,
    get_all_request_list,
    check_user_request_permission,
    get_all_users_list,
    update_user_last_login
)
from util.ldap_auth_middleware import CachedLDAPAuth
from datetime import datetime
from log_base import MyLog
log = MyLog().my_logger()
# 用户注册
def register():
    # 检查是否允许注册
    if not config.is_registration_allowed():
        return jsonify({'success': False, 'error': '系统当前不允许注册新用户'}), 403
    
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')
    
    if not username or not password:
        return jsonify({'success': False, 'error': '用户名和密码不能为空'}), 400
    
    # 检查用户名长度和格式
    if len(username) < 3 or len(username) > 20:
        return jsonify({'success': False, 'error': '用户名长度必须在3-20个字符之间'}), 400
    
    # 检查密码长度
    if len(password) < 6:
        return jsonify({'success': False, 'error': '密码长度至少为6个字符'}), 400
    
    # 确定用户角色：页面注册的用户默认为普通用户，除非在配置中指定为管理员
    final_role = 'admin' if config.is_admin_user(username) else config.get_default_role()
    
    # 记录日志
    log.info(f"用户注册请求: username={username}, requested_role={role}, final_role={final_role}")
    
    user_id = create_user(username, password, final_role)
    if user_id:
        return jsonify({
            'success': True, 
            'user_id': user_id,
            'role': final_role,
            'message': f'注册成功，用户角色为: {"管理员" if final_role == "admin" else "普通用户"}'
        })
    else:
        return jsonify({'success': False, 'error': '用户名已存在'}), 400

# 用户登录
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'error': '用户名和密码不能为空'}), 400
    
    # 首先尝试LDAP认证
    ldap_auth = CachedLDAPAuth()
    ldap_result = ldap_auth.authenticate(username, password)
    
    if ldap_result['success']:
        # LDAP认证成功，检查用户是否在数据库中
        user = get_user_by_username(username)
        
        if not user:
            # 用户不存在，自动创建用户
            user_id = create_user(username, 'LDAP_AUTH_NO_PASSWORD', 'user')
            if user_id:
                user = get_user_by_id(user_id)
            else:
                return jsonify({'success': False, 'error': '创建用户失败'}), 500
        else:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            update_user_last_login(timestamp, user['id'])
            user['last_login'] = timestamp
        # 生成JWT token
        token = generate_token(user['id'], user['username'], user['role'])
        if token:
            return jsonify({
                'success': True, 
                'user': user,
                'token': token,
                'auth_method': 'LDAP'
            })
        else:
            return jsonify({'success': False, 'error': 'Token生成失败'}), 500
    
    # LDAP认证失败，尝试数据库认证（兼容性）
    user = verify_user(username, password)
    if user:
        # 生成JWT token
        token = generate_token(user['id'], user['username'], user['role'])
        if token:
            return jsonify({
                'success': True, 
                'user': user,
                'token': token,
                'auth_method': 'Database'
            })
        else:
            return jsonify({'success': False, 'error': 'Token生成失败'}), 500
    else:
        return jsonify({'success': False, 'error': '用户名或密码错误'}), 401

# 获取用户信息
def get_user_info(user_id):
    user = get_user_by_id(user_id)
    if user:
        return jsonify({'success': True, 'user': user})
    else:
        return jsonify({'success': False, 'error': '用户不存在'}), 404

# 以下函数已删除，因为 UserRequestRelation 表已移除：
# - get_user_requests()
# - create_relation()

# 获取所有用户列表（管理员专用）
def get_all_users():
    try:
        users = get_all_users_list()
        return jsonify({
            'success': True,
            'data': users
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Token验证接口
def verify_token_api():
    """
    验证用户token的有效性
    """
    from auth import verify_token
    
    # 检查请求头中的Authorization
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return jsonify({'success': False, 'error': '缺少认证'}), 401
    
    # 检查Bearer token格式
    try:
        token_type, token = auth_header.split(' ', 1)
        if token_type.lower() != 'bearer':
            return jsonify({'success': False, 'error': '认证格式错误，应为Bearer token'}), 401
    except ValueError:
        return jsonify({'success': False, 'error': 'Authorization头格式错误'}), 401
    
    # 验证token
    payload = verify_token(token)
    if not payload:
        return jsonify({'success': False, 'error': 'Token无效或已过期'}), 401
    exp_timestamp = payload.get('exp')
    exp_time = datetime.fromtimestamp(exp_timestamp)
    log.info(f"Auth验证成功 - 用户名: {payload.get('username')}, 角色:{payload.get('role')}, 过期时间: {exp_time.strftime('%Y-%m-%d %H:%M:%S')}")
    # 返回验证成功信息
    return jsonify({
        'success': True,
        'user': {
            'user_id': payload.get('user_id'),
            'username': payload.get('username'),
            'role': payload.get('role')
        }
    })


# 以下函数已删除，因为 UserRequestRelation 表已移除：
# - get_all_requests()
# - assign_request_to_user()
# - unassign_request_from_user()