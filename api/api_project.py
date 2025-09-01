from flask import request, jsonify, g
from auth import require_auth, project_owner_permission,project_read_permission,project_write_permission
from util.xapi_res import XAPI_ERROR_RES,XAPI_SUCCESS_RES
from db_orm import (
    create_project, get_user_projects, get_project_by_id,
    check_user_project_permission,
    get_project_requests, add_project_request_relation,
    get_project_members, remove_project_member, get_all_projects ,grant_project_permission
)
from log_base import MyLog
log = MyLog().my_logger()
# 获取用户的项目列表
def get_projects():
    try:
        current_user_id = g.user_id
        user_role = g.role
        
        # 如果是管理员，获取所有项目；否则只获取用户有权限的项目
        if user_role == 'admin':
            projects = get_all_projects()
        else:
            projects = get_user_projects(current_user_id)
            
        return jsonify({
            'success': True,
            'projects': projects
        })
    except Exception as e:
        print(f"Error getting projects: {e}")
        return jsonify({'error': '获取项目列表失败'}), 500

# 创建新项目
@require_auth
def create_new_project():
    try:
        current_user_id = g.user_id
        data = request.get_json()
        user_role = g.role
        if user_role != 'admin':
            return jsonify({'error': '无权限操作'}), 400
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if not name:
            return jsonify({'error': '项目名称不能为空'}), 400
        
        project_id = create_project(name, description, current_user_id)
        if project_id:
            return jsonify({
                'success': True,
                'message': '项目创建成功',
                'project_id': project_id
            })
        else:
            return jsonify({'error': '项目创建失败，可能项目名称已存在'}), 400
    except Exception as e:
        print(f"Error creating project: {e}")
        return jsonify({'error': '创建项目失败'}), 500

# 获取项目详情
@project_read_permission
def get_project_detail(project_id):
    try:    
        project = get_project_by_id(project_id)
        if not project:
            return jsonify({'error': '项目不存在'}), 404
        
        return jsonify({
            'success': True,
            'project': project,
        })
    except Exception as e:
        print(f"Error getting project detail: {e}")
        return jsonify({'error': '获取项目详情失败'}), 500

# 获取项目的请求列表
@project_read_permission
def get_project_request_list(project_id):
    try:
        requests = get_project_requests(project_id)
        return jsonify({
            'success': True,
            'data': requests
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 获取项目成员列表
@project_read_permission
def get_project_members_list():
    try:
        project_id = request.args.get('project_id')
        if not project_id:
            return jsonify({'error': '项目ID不能为空'}), 400
        members = get_project_members(project_id)
        return jsonify({
            'success': True,
            'members': members
        })
    except Exception as e:
        print(f"Error getting project members: {e}")
        return jsonify({'error': '获取项目成员失败'}), 500

# 添加项目成员
@project_owner_permission
def add_project_member():
    try:
        current_user_id = g.user_id
        data = request.get_json()
        if not data:
            return XAPI_ERROR_RES('请求数据为空', 400)
        user_id = data.get('user_id')
        project_id = data.get('project_id')
        permission_level = data.get('permission_level', 'read')
        log.info(f"项目：{project_id},操作：{current_user_id}，user_id:{user_id},{permission_level}")
        if not project_id or not user_id:
            return XAPI_ERROR_RES('项目ID和用户ID不能为空', 400)
        # 验证权限级别
        if permission_level not in ['read', 'write', 'owner']:
            return XAPI_ERROR_RES(f'无效的权限级别{permission_level}', 400)

        success = grant_project_permission(user_id, project_id, permission_level, current_user_id)
        if success:
            return jsonify({
                'success': True,
                'message': '添加项目成员成功'
            })
        else:
            return XAPI_ERROR_RES('添加项目成员失败', 500)
    except Exception as e:
        print(f"Error adding project member: {e}")
        return XAPI_ERROR_RES('添加项目成员失败', 500)

# 移除项目成员
@project_owner_permission
def remove_project_member_api():
    try:
        data = request.get_json()
        if not data:
            return XAPI_ERROR_RES('请求数据为空', 400)
        current_user_id = g.user_id    
        project_id = data.get('project_id')
        user_id = data.get('user_id')
        log.info(f"项目：{project_id},操作：{current_user_id}，user_id:{user_id}")
        # 不能移除自己
        if current_user_id == user_id:
            return XAPI_ERROR_RES('不能移除自己', 400)

        success = remove_project_member(user_id, project_id)
        if success:
            return jsonify({
                'success': True,
                'message': '移除项目成员成功'
            })
        else:
            return XAPI_ERROR_RES('移除项目成员失败，可能该用户不是项目成员', 400)
    except Exception as e:
        print(f"Error removing project member: {e}")
        return XAPI_ERROR_RES('移除项目成员失败', 400)
