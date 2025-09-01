from flask import jsonify, Response
from typing import Tuple, Dict, Any
from log_base import MyLog
log = MyLog().my_logger()

def XAPI_SUCCESS_RES(
    status_code: int = 200,
    **kwargs: Any # 允许直接传入键值对作为响应数据
) -> Tuple[Response, int]:
    response_payload = {'success': True}
    # 将所有传入的 kwargs 合并到响应负载中
    response_payload.update(kwargs)
    return jsonify(response_payload), status_code

def XAPI_ERROR_RES(
        message: str,
        status_code: int = 500,
        **kwargs: Any
) -> Tuple[Response, int]:
    """创建一个标准化的 JSON 错误响应。"""
    error_payload = {'error': message}
    log.info(error_payload)
    error_payload.update(kwargs)
    return jsonify(error_payload), status_code
def XAPI_RES(
        message: str,
        success: bool = True,
        status_code: int = 200,
        **kwargs: Any
) -> Tuple[Response, int]:
    """创建一个标准化的 JSON 错误响应。"""
    payload = {'msg': message,'success': success} 
    log.info(payload)
    payload.update(kwargs)
    return jsonify(payload), status_code
