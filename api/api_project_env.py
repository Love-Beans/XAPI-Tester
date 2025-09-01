from flask import Blueprint, request, jsonify, g
from auth import project_owner_permission,project_read_permission
from db_orm import get_project_env, save_project_env, delete_project_env
import json
from util.xapi_res import XAPI_ERROR_RES, XAPI_SUCCESS_RES, XAPI_RES
from log_base import MyLog
log = MyLog().my_logger()


@project_read_permission
def get_env(project_id):
    """获取项目环境配置"""
    try:
        env_data = get_project_env(project_id)
        if env_data:
            # 解析JSON字符串
            env_data['env'] = json.loads(env_data['env']) if env_data['env'] else {}
            return XAPI_RES('OK',True, 200,data=env_data)
        else:
            # 返回默认结构
            return XAPI_RES('OK',True, 200, data={
                    'project_id': project_id,
                    'env': {
                        'host': {
                            'dev_host': '',
                            'pre_host': '',
                            'pro_host': ''
                        },
                        'token': ''
                    }
                })
    except Exception as e:
        log.error(f'获取环境配置失败{e}')
        return XAPI_RES('获取环境配置失败',False, 500)

@project_owner_permission
def save_env(project_id):
    """保存项目环境配置"""
    try:
        data = request.get_json()
        env_config = data.get('env', {})
        
        # 将环境配置转换为JSON字符串
        env_json = json.dumps(env_config, ensure_ascii=False)
        
        save_project_env(project_id, env_json)
        return XAPI_RES('环境配置保存成功',True, 200)
    except Exception as e:
        log.error(f'保存环境配置时出错：{e}')
        return XAPI_RES('保存环境配置失败',False, 500)

@project_owner_permission
def delete_env(project_id):
    """删除项目环境配置"""
    try:
        delete_project_env(project_id)
        return XAPI_RES('环境配置删除成功',True, 200)
    except Exception as e:
        log.error(f'删除环境配置时出错：{e}')
        return XAPI_RES('删除环境配置失败',False, 500)