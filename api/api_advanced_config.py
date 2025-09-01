from flask import Blueprint, request, jsonify, g
from db_orm import save_advanced_config, get_advanced_config, delete_advanced_config
from auth import require_auth, project_owner_permission, project_write_permission, project_read_permission
import json

advanced_config_bp = Blueprint('advanced_config', __name__)

@advanced_config_bp.route('/api/advanced-config', methods=['POST'])
@require_auth
@project_write_permission
def save_config():
    """保存高级配置"""
    try:
        data = request.get_json()
        project_id = data.get('project_id')
        private_request_id = data.get('private_request_id')
        request_info_id = data.get('request_info_id')
        is_global = data.get('is_global', 0)
        body_info = data.get('body_info', {}) if data.get('body_info') else None
        query_info = data.get('query_info', {}) if data.get('query_info') else None
        request_name = data.get('request_name')
        host = data.get('host')
        
        # 类型转换
        try:
            project_id = int(project_id) if project_id else 0
            private_request_id = int(private_request_id) if private_request_id else None
            request_info_id = int(request_info_id) if request_info_id else None
        except (ValueError, TypeError):
            return jsonify({'error': '项目ID或请求ID格式无效'}), 400
        
        if not project_id or project_id <= 0:
            return jsonify({'error': '项目ID无效'}), 400
        
        # 如果不是全局配置，front_request_id 必须提供
        if not is_global and not private_request_id:
            return jsonify({'error': '非全局配置必须提供前端请求ID'}), 400
        
        success = save_advanced_config(project_id, request_info_id, is_global, body_info, query_info, request_name, private_request_id, host)
        
        if success:
            return jsonify({'message': '配置保存成功'})
        else:
            return jsonify({'error': '配置保存失败'}), 500
            
    except Exception as e:
        return jsonify({'error': f'保存配置时发生错误: {str(e)}'}), 500

# @advanced_config_bp.route('/api/advanced-config/<int:project_id>', methods=['GET'])
# def get_config(project_id):
#     """获取高级配置"""
#     try:
#         private_request_id = request.args.get('private_request_id', type=int)
#         is_global = request.args.get('is_global')
        
#         # 转换is_global参数
#         if is_global is not None:
#             is_global = is_global.lower() == 'true'
        
    #     configs = get_advanced_config(project_id, private_request_id, is_global)
        
    #     # 解析JSON字段
    #     for config in configs:
    #         if config.get('body_info'):
    #             try:
    #                 config['body_info'] = json.loads(config['body_info'])
    #             except:
    #                 config['body_info'] = {}
    #         else:
    #             config['body_info'] = {}
                
    #         if config.get('query_info'):
    #             try:
    #                 config['query_info'] = json.loads(config['query_info'])
    #             except:
    #                 config['query_info'] = {}
    #         else:
    #             config['query_info'] = {}
        
    #     return jsonify({'configs': configs})
        
    # except Exception as e:
    #     return jsonify({'error': f'获取配置时发生错误: {str(e)}'}), 500

@advanced_config_bp.route('/api/advanced-config/list', methods=['GET'])
@require_auth
@project_read_permission
def get_config_list():
    """获取高级配置列表（支持分页）"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        project_id = request.args.get('project_id', type=int)
        is_global = request.args.get('is_global')
        private_request_id = request.args.get('private_request_id', type=int)
        if not project_id:
            return jsonify({
                'configs':[],
                'total':0,
                'error': '项目ID不能为空'}), 200
        
        # 转换is_global参数
        if is_global is not None:
            is_global = is_global.lower() == 'true'
        
        configs = get_advanced_config(project_id, private_request_id=private_request_id, is_global=is_global)
        # 简单分页处理
        total = len(configs)
        start = (page - 1) * limit
        end = start + limit
        paginated_configs = configs[start:end]
        
        return jsonify({
            'configs': paginated_configs,
            'total': total,
            'page': page,
            'limit': limit,
            'total_pages': (total + limit - 1) // limit
        })
        
    except Exception as e:
        return jsonify({'error': f'获取配置列表时发生错误: {str(e)}'}), 500


@advanced_config_bp.route('/api/advanced-config/<int:config_id>', methods=['PUT'])
@require_auth
@project_write_permission
def update_config(config_id):
    """更新高级配置"""
    try:
        data = request.get_json()
        project_id = data.get('project_id')
        request_info_id = data.get('request_info_id')
        is_global = data.get('is_global', 0)
        body_info = data.get('body_info', '') if data.get('body_info') else ''
        query_info = data.get('query_info', '') if data.get('query_info') else ''
        request_name = data.get('request_name')
        private_request_id = data.get('private_request_id')
        host = data.get('host')

        # 类型转换
        try:
            project_id = int(project_id) if project_id else 0
            request_info_id = int(request_info_id) if request_info_id else None
        except (ValueError, TypeError):
            return jsonify({'error': '项目ID或请求ID格式无效'}), 400
        
        if not project_id or project_id <= 0:
            return jsonify({'error': '项目ID无效'}), 400
        
        # 如果不是全局配置，request_info_id 必须提供
        if not is_global and not request_info_id:
            return jsonify({'error': '非全局配置必须提供请求ID'}), 400
        
        # 更新配置
        from db_orm import update_advanced_config
        success = update_advanced_config(config_id, project_id, request_info_id, is_global, body_info, query_info,request_name= request_name,private_request_id=private_request_id, host=host)
        
        if success:
            return jsonify({'message': '配置更新成功'})
        else:
            return jsonify({'error': '配置更新失败'}), 500
            
    except Exception as e:
        return jsonify({'error': f'更新配置时发生错误: {str(e)}'}), 500

@advanced_config_bp.route('/api/advanced-config/<int:config_id>', methods=['DELETE'])
@require_auth
@project_write_permission
def delete_config(config_id):
    """删除高级配置"""
    try:
        success = delete_advanced_config(config_id)
        
        if success:
            return jsonify({'message': '配置删除成功'})
        else:
            return jsonify({'error': '配置删除失败'}), 500
            
    except Exception as e:
        return jsonify({'error': f'删除配置时发生错误: {str(e)}'}), 500