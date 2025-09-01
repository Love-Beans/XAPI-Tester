import os
import json
import time
from datetime import datetime
import requests
from urllib.parse import quote
from flask import Flask, request, jsonify, Response, send_from_directory, g
from util.xapi_res import XAPI_RES
from auth import project_read_permission, project_write_permission
from util.xapi_replace import replace_variables, contains_xapi_variables
# 导入数据库操作模块
from db_orm import (
    save_or_update_request_info,
    save_to_history, 
    get_request_info_list,
    get_all_request_list,
    get_history_by_request_info_id,
    get_request_info_by_id,
    add_project_request_relation,
    get_advanced_config,
    copy_request_info,
    delete_request_info
)
from log_base import MyLog
log = MyLog().my_logger()


# 全局前置请求方法
def execute_global_pre_request(project_id):
    """
    执行全局前置请求
    通过project_id查询advanced_config中的request_info_id，获取请求信息并发起前置请求
    返回格式：{"global": {"request_id_1": {"header": "", "body": ""}, "request_id_2": {"header": "", "body": ""}}}
    """
    try:
        # 查询全局配置
        global_configs = get_advanced_config(project_id, is_global=True)
        
        result = {"global": {}}
        
        for config in global_configs:
            request_info_id = config.get('request_info_id')
            if not request_info_id:
                continue
                
            # 获取请求信息
            request_info = get_request_info_by_id(request_info_id)
            if not request_info:
                continue
                
            # 解析配置中的body和query信息
            body_info = config.get('body_info',{})
            query_info = config.get('query_info',{})    
            host = config.get('host',"")   
            url = request_info['url']
            # 构建请求URL - 如果提供了host，则拼接host和路径
            if host and not url.startswith('http'):
                # 确保host不以/结尾，url以/开头
                host = host.rstrip('/')
                url = url if url.startswith('/') else '/' + url
                url = host + url
            log.info(f"global -- body_info：{type(body_info)},headers{type(request_info.get('headers', '{}'))},query_info{type(query_info)},url:{url}")
            # 准备请求参数
            headers = request_info.get('headers', '{}')
            method = request_info['method']
            url_encoded, request_body =request_info_parser(url, body_info ,json.loads(query_info))
            try:
                response = xapi_send_request(url_encoded, method, headers, request_body)
                # 保存响应结果
                response_headers = dict(response.headers)
                try:
                    response_body = response.json()
                except:
                    response_body = response.text
                
                result["global"][str(config.get('id'))] = {
                    "header": response_headers,
                    "body": response_body
                }
                
                log.info(f"全局前置请求成功 - request_id: {request_info_id}, status: {response.status_code}")
                
            except Exception as e:
                log.error(f"全局前置请求失败 - request_id: {request_info_id}, error: {str(e)}")
                result["global"][str(config.get('id'))] = {
                    "header": {},
                    "body": f"请求失败: {str(e)}"
                }
        
        return result
        
    except Exception as e:
        log.error(f"执行全局前置请求异常: {str(e)}")
        return {"global": {}}

# 自定义前置请求方法
def execute_custom_pre_request(project_id, request_id):
    """
    执行自定义前置请求
    通过project_id和request_id查询advanced_config中的private_request_id，获取请求信息并发起前置请求
    返回格式：{"request_id_1": {"header": "", "body": ""}, "request_id_2": {"header": "", "body": ""}}
    """
    try:
        # 查询自定义配置
        custom_configs = get_advanced_config(project_id, is_global=False, private_request_id=request_id)
        
        result = {"custom": {}}
        
        for config in custom_configs:
            request_info_id = config.get('request_info_id')
            if not request_info_id:
                continue
                
            # 获取请求信息
            request_info = get_request_info_by_id(request_info_id)
            if not request_info:
                continue
                
            # 解析配置中的body和query信息
            body_info = config.get('body_info',{})
            query_info = config.get('query_info',{})  
            host = config.get('host',"")        
            # 构建请求URL - 如果提供了host，则拼接host和路径
            url = request_info['url']
            if host and not url.startswith('http'):
                # 确保host不以/结尾，url以/开头
                host = host.rstrip('/')
                url = url if url.startswith('/') else '/' + url
                url = host + url
            log.info(f"custom -- body_info：{type(body_info)},headers{type(request_info.get('headers', '{}'))},query_info{type(query_info)},url:{url}")
            # 准备请求参数
            headers = request_info.get('headers', '{}')
            method = request_info['method']
            url_encoded, request_body =request_info_parser(url, body_info ,json.loads(query_info))
            
            try:
                response = xapi_send_request(url_encoded, method, headers, request_body)
                # 保存响应结果
                response_headers = dict(response.headers)
                try:
                    response_body = response.json()
                except:
                    response_body = response.text
                
                result["custom"][str(config.get('id'))] = {
                    "header": response_headers,
                    "body": response_body
                }
                
                log.info(f"自定义前置请求成功 - request_id: {request_info_id}, status: {response.status_code}")
                
            except Exception as e:
                log.error(f"自定义前置请求失败 - request_id: {request_info_id}, error: {str(e)}")
                result["custom"][str(config.get('id'))] = {
                    "header": {},
                    "body": f"请求失败: {str(e)}"
                }
        return result
        
    except Exception as e:
        log.error(f"执行自定义前置请求异常: {str(e)}")
        return {}

# 路由：发送API请求
@project_read_permission
def send_request():
    data = request.json
    
    if not data or 'url' not in data or 'method' not in data:
        return XAPI_ERROR_RES('Missing required fields', 400)

    url = data['url']
    method = data['method']
    headers = data.get('headers', {})
    auth = data.get('auth', {})
    body = data.get('body', '')
    query = data.get('query', {})
    request_name = data.get('request_name', '')
    request_info_id = data.get('request_info_id', None)
    user_id = g.user_id  # 新增用户ID参数
    project_id = data.get('project_id')
    username = g.username
    
    # 检查URL的host是否为127.0.0.1，如果是则替换为客户端IP
    if '127.0.0.1' in url:
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        if client_ip:
            # 如果有多个IP（通过代理），取第一个
            if ',' in client_ip:
                client_ip = client_ip.split(',')[0].strip()
            url = url.replace('127.0.0.1', client_ip)
            log.info(f"URL中的127.0.0.1已替换为客户端IP: {client_ip}，新URL: {url}")
    # 检查 body 和 query 中是否包含 $xapi 变量
    needs_pre_request = contains_xapi_variables(body) or contains_xapi_variables(query) or contains_xapi_variables(headers)
    
    # 执行前置请求（仅在需要时）
    pre_request_results = {}
    if project_id and needs_pre_request:   
        log.info(f"检测到 $xapi 变量，开始执行前置请求 - project_id: {project_id}")
        
        # 没有request_id，执行全局前置请求
        log.info(f"执行全局前置请求 - project_id: {project_id}")
        global_results = execute_global_pre_request(project_id)
        if global_results:
            pre_request_results.update(global_results) 
            
        if request_info_id:
            # 有request_id，执行自定义前置请求
            log.info(f"执行自定义前置请求 - project_id: {project_id}, request_id: {request_info_id}")
            custom_results = execute_custom_pre_request(project_id, request_info_id)
            if custom_results:
                pre_request_results.update(custom_results)
    elif project_id:
        log.info(f"未检测到 $xapi 变量，跳过前置请求 - project_id: {project_id}")

    # 变量替换：在发送请求前替换 body 和 query 中的变量
    if pre_request_results:
        log.info(f"开始变量替换，前置请求结果: {json.dumps(pre_request_results, ensure_ascii=False, indent=2)}")
        
        # 替换 body 中的变量
        original_body = body
        body = replace_variables(body, pre_request_results)
        if body != original_body:
            log.info(f"Body 变量替换: {original_body} -> {body}")
        
        # 替换 query 中的变量
        original_query = query
        query = replace_variables(query, pre_request_results)
        if query != original_query:
            log.info(f"Query 变量替换: {json.dumps(original_query, ensure_ascii=False)} -> {json.dumps(query, ensure_ascii=False)}")
        
        original_headers = headers
        headers = replace_variables(headers, pre_request_results)
        if headers != original_headers:
            log.info(f"Headers 变量替换: {json.dumps(original_headers, ensure_ascii=False)} -> {json.dumps(headers, ensure_ascii=False)}")
        
    # 打印请求信息，便于调试
    log.info(f"\nproject:{project_id},用户:{user_id},请求信息 - {datetime.now()},URL: {url}, Method: {method}, 请求名称: {request_name}")
    print(f"Headers: {json.dumps(headers, ensure_ascii=False, indent=2)}")
    print(f"Auth: {json.dumps(auth, ensure_ascii=False, indent=2)}")
    print(f"Query: {json.dumps(query, ensure_ascii=False, indent=2)}\n")
    
    # 记录开始时间
    start_time = time.time()
    
    try:
        url_encoded, request_body =request_info_parser(url, body ,query)
        # 发送请求
        response = xapi_send_request(url_encoded, method, headers, request_body)
        
        # 计算响应时间（毫秒）
        response_time = int((time.time() - start_time) * 1000)
            # 处理流式响应
        if headers.get('Accept') == 'text/event-stream' or 'stream' in data and data['stream']:
            # 对于流式响应，直接转发数据
            def generate():
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        yield chunk
            
            # 保存到历史记录（只保存前一部分数据用于历史记录）
            response_preview = next(response.iter_lines(), b'').decode('utf-8', errors='ignore')
            
            # 只有存在request_info_id时才记录历史
            if request_info_id:
                history_id = save_to_history(
                    request_info_id=request_info_id,
                    response_status=response.status_code,
                    response_headers=dict(response.headers),
                    response_body=response_preview,
                    response_time=response_time,
                    url=url,
                    method=method,
                    auth=auth,
                    request_name=request_name,
                    query=query,
                    request_headers=headers,
                    request_body=body,
                    execution_status="成功" if response.status_code < 400 else "失败",
                    execution_message=f"HTTP {response.status_code} - {response_time}ms",
                    execution_details={
                        "contentType": response.headers.get('Content-Type'),
                        "contentLength": response.headers.get('Content-Length'),
                        "statusCode": response.status_code
                    }
                )
            
            return Response(generate(), 
                        status=response.status_code,
                        headers=dict(response.headers))
        # 打印响应信息
        log.info(f"\n响应信息- 状态码: {response.status_code},响应时间: {response_time} ms,响应头: {json.dumps(dict(response.headers), ensure_ascii=False, indent=2)}")
        
        # 尝试解析响应体为JSON
        try:
            # 先检查响应内容是否为空
            if response.text.strip():
                response_body = response.json()
                response_body_str = json.dumps(response_body)
            else:
                response_body = ""
                response_body_str = ""
                print(f"响应体: (空响应)\n")
        except json.JSONDecodeError as e:
            response_body = response.text
            response_body_str = response_body
            print(f"响应体: {response.text}\n")
            log.warning(f"响应体不是有效的JSON格式: {str(e)}")
        except Exception as e:
            response_body = response.text
            response_body_str = response_body
            print(f"响应体: {response.text}\n")
            log.warning(f"解析响应体时发生错误: {str(e)}")
        
        # 设置执行状态信息
        status = "成功" if response.status_code < 400 else "失败"
        message = f"HTTP {response.status_code} - {response_time}ms"
        details = {
            "contentType": response.headers.get('Content-Type'),
            "contentLength": response.headers.get('Content-Length'),
            "statusCode": response.status_code
        }
        
        # 只有存在request_info_id时才记录历史
        if request_info_id:
            history_id = save_to_history(
                request_info_id=request_info_id,
                response_status=response.status_code,
                response_headers=dict(response.headers),
                response_body=response_body_str,
                response_time=response_time,
                url=url,
                method=method,
                auth=auth,
                request_name=request_name,
                query=query,
                request_headers=headers,
                request_body=body,
                execution_status=status,
                execution_message=message,
                execution_details=details,
                pre_request_results=pre_request_results,
                username=username
            )
        
        # 返回响应（包含请求信息以便前端保存）
        return jsonify({
            'status': response.status_code,
            'headers': dict(response.headers),
            'request_info': {
                'url': data['url'],
                'method': method,
                'headers': headers,
                'body': body,
                'query': query,
                'auth': auth,
                'request_name': request_name
            },
            'response_time': response_time,
            'execution_status': status,
            'execution_message': message,
            'execution_details': details,
            'body': response_body,
            'responseTime': response_time,
            'pre_request_results': pre_request_results  # 添加前置请求结果
        })
        
    except Exception as e:
        # 记录异常状态
        error_message = str(e)
        log.info(f"请求异常: {error_message}")
        
        # 只有存在request_info_id时才记录历史（失败状态）
        if request_info_id:
            history_id = save_to_history(
                request_info_id=request_info_id,
                response_status=500,
                response_headers={},
                response_body=json.dumps({"error": error_message}),
                response_time=int((time.time() - start_time) * 1000),
                url=url,
                method=method,
                auth=auth,
                request_name=request_name,
                query=query,
                request_headers=headers,
                request_body=body,
                execution_status="异常",
                execution_message=error_message,
                execution_details={"exception": error_message}
            )
            
        return jsonify({
            'error': error_message,
            'pre_request_results': pre_request_results  # 即使异常也返回前置请求结果
        }), 500
@project_write_permission
def save_request_info():
    data = request.json
    project_id = data.get('project_id')

    if not data:
        return XAPI_ERROR_RES('Missing request data', 400)
    if not project_id:
        return XAPI_ERROR_RES('project_id not found', 400)

    # 检查必填字段
    request_name = data.get('request_name', '').strip()
    if not request_name:
        return XAPI_ERROR_RES('请求名称不能为空', 400)

    # 保存或更新请求信息 - 依赖db_operations.py的逻辑
    # 如果request_name存在则更新，不存在则新增
    info_id = save_or_update_request_info(
        url=data.get('url'),
        method=data.get('method'),
        headers=data.get('headers', {}),
        body=data.get('body', ''),
        query=data.get('query', {}),
        auth=data.get('auth', {}),
        request_name=request_name,
        request_info_id=data.get('request_info_id', {}),  # 不传递request_info_id，完全依赖request_name
    )
    
    if not info_id:
        return jsonify({'error': 'Failed to save request info'}), 500
    
    # 如果提供了project_id，建立项目与请求的关联
    try:
        success = add_project_request_relation(project_id, info_id)
        if not success:
            log.info(f"Warning: Failed to associate request {info_id} with project {project_id}")
    except Exception as e:
        log.info(f"Error associating request with project: {e}")
    
    return jsonify({
        'success': True,
        'request_info_id': info_id
    })

def get_request_info():
    # 检查是否提供了用户信息（用于权限控制）
    user_id = g.user_id
    user_role = g.role

    try:
        if user_id and user_role:
            # 基于权限返回请求列表
            if user_role == 'admin':
                # 管理员可以查看所有请求
                request_info_list = get_all_request_list()
            else:
                # 普通用户暂时无法查看请求（UserRequestRelation 表已删除）
                request_info_list = []
        else:
            # 兼容旧版本，返回所有请求（无权限控制）
            return jsonify({
                'success': False,
                'error': "无权限"
            }), 401
        
        return jsonify({
            'success': True,
            'data': request_info_list
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 路由：获取特定请求的历史记录
@project_read_permission
def get_request_history(request_info_id):
    try:
        history = get_history_by_request_info_id(request_info_id)
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def request_info_parser(url,body_info,query_info):
    print(f"Type-body: {type(body_info)},Type-query: {type(query_info)}")
    url_encoded=url
    request_body = None
    try:
        # if type(body_info)==str:
        #     body_info=json.loads(body_info)
        # if type(query_info)==str:
        #     query_info=json.loads(query_info)
        # 处理查询参数，拼接到URL后面
        if query_info:
            # 构建查询字符串
            query_params = []
            for key, value in query_info.items():
                if value: 
                    # 对参数值进行URL编码
                    encoded_value = quote(str(value), safe='')
                    query_params.append(f"{key}={encoded_value}")                
            
            if query_params:
                # 检查URL是否已经包含查询参数
                separator = '&' if '?' in url else '?'
                url_encoded = url + separator + '&'.join(query_params)
        
        log.info(f"最终请求URL: {url_encoded}")
                # 处理请求体编码    
        if body_info:
            # 如果body是字符串且包含中文，确保使用UTF-8编码
            if isinstance(body_info, str):
                request_body = body_info.encode('utf-8')
            else:
                request_body = body_info
    except Exception as e:
        log.error(f"请求失败: {e}")
    return url_encoded, request_body

def xapi_send_request(url_encoded, method, headers, request_body):
    log.info(f"最终请求request_body: {request_body}")
    #print(f"Body: {json.dumps(request_body, ensure_ascii=False, indent=2)}\n")
    if method == 'GET':
        response = requests.get(url_encoded, headers=headers, stream=True)
    elif method == 'POST':
        # 检查Content-Type是否设置
        if 'Content-Type' not in headers and request_body:
            log.warn("警告: 未设置Content-Type，可能导致415错误")
            log.warn("自动添加Content-Type: application/json")
            headers['Content-Type'] = 'application/json'
        response = requests.post(url_encoded, headers=headers, data=request_body, stream=True)
    elif method == 'PUT':
        if 'Content-Type' not in headers and request_body:
            log.warn("警告: 未设置Content-Type，可能导致415错误")
            log.warn("自动添加Content-Type: application/json")
            headers['Content-Type'] = 'application/json'
        response = requests.put(url_encoded, headers=headers, data=request_body, stream=True)
    elif method == 'DELETE':
        response = requests.delete(url_encoded, headers=headers, stream=True)
    elif method == 'PATCH':
        if 'Content-Type' not in headers and request_body:
            log.warn("警告: 未设置Content-Type，可能导致415错误")
            log.warn("自动添加Content-Type: application/json")
            headers['Content-Type'] = 'application/json'
        response = requests.patch(url_encoded, headers=headers, data=request_body, stream=True)
    else:
        response = None
    return response

@project_write_permission
def copy_request():
    """
    复制请求信息
    """
    try:
        data = request.get_json()
        request_id = data.get('request_id')
        project_id = data.get('project_id')
        
        if not request_id or not project_id:
            return XAPI_RES("缺少必要参数",False,400)
        
        new_request_id = copy_request_info(request_id, project_id)
        if new_request_id:
            return XAPI_RES("复制成功", True, 200)
        else:
            return XAPI_RES("复制失败", False, 500)
            
    except Exception as e:
        log.error(f"复制请求时发生错误: {str(e)}")
        return XAPI_RES(f"复制请求时发生错误",False,500)

@project_write_permission
def delete_request():
    """
    删除请求信息
    """
    try:
        data = request.get_json()
        request_id = data.get('request_id')
        project_id = data.get('project_id')
        
        if not request_id or not project_id:
            return XAPI_RES("缺少必要参数",False,400)
        
        success = delete_request_info(request_id, project_id)
        if success:
            return XAPI_RES("删除成功", True, 200)
        else:
            return XAPI_RES("删除失败", False, 500)
            
    except Exception as e:
        log.error(f"删除请求时发生错误: {str(e)}")
        return XAPI_RES(f"删除请求时发生错误",False,500)