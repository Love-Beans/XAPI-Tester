import os
import json
import time
import re
from log_base import MyLog
log = MyLog().my_logger()
# 检查是否需要执行前置请求（只有当包含 $xapi 变量时才执行）
def contains_xapi_variables(data):
    """检查数据中是否包含 $xapi 变量"""
    if isinstance(data, str):
        return bool(re.search(r'\$xapi\.(custom|global)\.\d+\.(body|header)\.[\w\.]+', data))
    elif isinstance(data, dict):
        return any(contains_xapi_variables(value) for value in data.values())
    elif isinstance(data, list):
        return any(contains_xapi_variables(item) for item in data)
    return False
# 变量替换函数
def replace_variables(data, pre_request_results):
    """
    替换数据中的变量，支持格式：
    $xapi.custom.1.body.xxx - 从自定义前置请求结果中获取
    $xapi.global.10.header.authorization - 从全局前置请求结果中获取
    """
    def replace_value(value):
        if not isinstance(value, str):
            return value
            
        # 匹配 $xapi.custom.{id}.{type}.{path} 或 $xapi.global.{id}.{type}.{path}
        pattern = r'\$xapi\.(custom|global)\.(\d+)\.(body|header)\.([\w\.]+)'
        
        def replacer(match):
            request_type = match.group(1)  # custom 或 global
            request_id = match.group(2)    # 请求ID
            data_type = match.group(3)     # body 或 header
            path = match.group(4)          # 属性路径
            log.info(f"request_type: {request_type}, request_id: {request_id}, data_type: {data_type}, path: {path}")
            try:
                # 从 pre_request_results 中获取数据
                if request_type in pre_request_results and request_id in pre_request_results[request_type]:
                    source_data = pre_request_results[request_type][request_id].get(data_type, {})
                    
                    # 支持嵌套路径，如 error.message
                    current_value = source_data
                    for key in path.split('.'):
                        if isinstance(current_value, dict) and key in current_value:
                            current_value = current_value[key]
                        else:
                            log.error(f"路径不存在，返回原始变量: {match.group(0) }")
                            return match.group(0)  # 如果路径不存在，返回原始变量
                    
                    return str(current_value)
                else:
                    log.error(f"数据不存在，返回原始变量: {match.group(0) }")
                    return match.group(0)  # 如果数据不存在，返回原始变量
            except Exception as e:
                log.warning(f"变量替换失败: {match.group(0)}, 错误: {str(e)}")
                return match.group(0)
        
        return re.sub(pattern, replacer, value)
    
    def recursive_replace(obj):
        if isinstance(obj, dict):
            return {key: recursive_replace(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [recursive_replace(item) for item in obj]
        elif isinstance(obj, str):
            return replace_value(obj)
        else:
            return obj
    
    return recursive_replace(data)