
import jwt
import datetime
from functools import wraps
from flask import request, jsonify, current_app, g
from db_orm import get_user_by_id, check_user_project_permission
from config import JWT_SECRET_KEY
from log_base import MyLog
log = MyLog().my_logger()

# JWT算法
JWT_ALGORITHM = 'HS256'

def generate_token(user_id, username, role):
    """
    生成JWT token
    """
    try:
        # 设置过期时间为7天
        expiration_time = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        
        payload = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'exp': expiration_time,
            'iat': datetime.datetime.utcnow()  # 签发时间
        }
        
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token
    except Exception as e:
        log.error(f"Token generation error: {e}")
        return None

def verify_token(token):
    """
    验证JWT token
    """
    try:
        # 解码token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # 打印用户信息和过期时间
        username = payload.get('username')
        exp_timestamp = payload.get('exp')
        role = payload.get('role')        
        # log.info(f"Auth验证成功 - 用户名: {username}, 角色:{role}, 过期时间: {exp_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return payload
    except jwt.ExpiredSignatureError:
        print("Token已过期")
        return None
    except jwt.InvalidTokenError as e:
        print(f"Token验证失败: {e}")
        return None

def require_auth(f):
    """
    鉴权装饰器
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
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
        
        # 将用户信息添加到请求上下文中
        # request.user_id = payload.get('user_id')
        # request.username = payload.get('username')
        # request.role = payload.get('role')
        g.user_id = payload.get('user_id')
        g.username = payload.get('username')
        g.role = payload.get('role')
        return f(*args, **kwargs)
    
    return decorated_function

def project_owner_permission(f):
    """
    管理权限装饰器
    admin用户：通过user_role判断
    普通用户：通过check_user_project_permission判断
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):        
        # 检查管理权限
        user_role = g.role
        
        # 如果是admin用户，直接允许访问
        if user_role == 'admin':
            return f(*args, **kwargs)
        
        # 普通用户需要检查项目权限
        # 从请求参数中获取project_id
        project_id = None
        
        # 首先尝试从URL路径参数获取（通过kwargs）
        if 'project_id' in kwargs:
            project_id = kwargs['project_id']
        # 然后尝试从查询参数获取
        elif request.method == 'GET':
            project_id = request.args.get('project_id')
        # 最后尝试从请求体获取
        elif request.method in ['POST', 'PUT', 'DELETE']:
            if request.is_json:
                data = request.get_json()
                project_id = data.get('project_id') if data else None
            else:
                project_id = request.form.get('project_id')
        
        if not project_id:
            return jsonify({'success': False, 'error': '缺少project_id参数'}), 400
        
        # 检查用户对该项目的权限
        permission = check_user_project_permission(g.user_id, project_id)
        if permission not in ['owner']:
                return jsonify({'error': '无权限修改该项目'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function
def project_write_permission(f):
    """
    管理权限装饰器
    admin用户：通过user_role判断
    普通用户：通过check_user_project_permission判断
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):        
        # 检查管理权限
        user_role = g.role
        
        # 如果是admin用户，直接允许访问
        if user_role == 'admin':
            return f(*args, **kwargs)
        
        # 普通用户需要检查项目权限
        # 从请求参数中获取project_id
        project_id = None
        
        # 首先尝试从URL路径参数获取（通过kwargs）
        if 'project_id' in kwargs:
            project_id = kwargs['project_id']
        # 然后尝试从查询参数获取
        elif request.method == 'GET':
            project_id = request.args.get('project_id')
        # 最后尝试从请求体获取
        elif request.method in ['POST', 'PUT', 'DELETE']:
            if request.is_json:
                data = request.get_json()
                project_id = data.get('project_id') if data else None
            else:
                project_id = request.form.get('project_id')
        
        if not project_id:
            return jsonify({'success': False, 'error': '缺少project_id参数'}), 400
        
        # 检查用户对该项目的权限
        permission = check_user_project_permission(g.user_id, project_id)
        if permission not in ['write', 'owner']:
                return jsonify({'error': '无权限修改该项目'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def project_read_permission(f):
    """
    管理权限装饰器
    admin用户：通过user_role判断
    普通用户：通过check_user_project_permission判断
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):        
        # 检查管理权限
        user_role = g.role
        
        # 如果是admin用户，直接允许访问
        if user_role == 'admin':
            return f(*args, **kwargs)
        
        # 普通用户需要检查项目权限
        # 从请求参数中获取project_id
        project_id = None
        
        # 首先尝试从URL路径参数获取（通过kwargs）
        if 'project_id' in kwargs:
            project_id = kwargs['project_id']
        # 然后尝试从查询参数获取
        elif request.method == 'GET':
            project_id = request.args.get('project_id')
        # 最后尝试从请求体获取
        elif request.method in ['POST', 'PUT', 'DELETE']:
            if request.is_json:
                data = request.get_json()
                project_id = data.get('project_id') if data else None
            else:
                project_id = request.form.get('project_id')
        
        if not project_id:
            return jsonify({'success': False, 'error': '缺少project_id参数'}), 400
        
        # 检查用户对该项目的权限
        permission = check_user_project_permission(g.user_id, project_id)
        if permission not in ['read', 'write', 'owner']:
                return jsonify({'error': '无权限访问该项目'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function
