from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class RequestInfo(Base):
    """API请求信息表"""
    __tablename__ = 'request_info'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(String(50), nullable=False)
    url = Column(Text, nullable=False)
    method = Column(String(10), nullable=False)
    headers = Column(Text)  # JSON字符串
    body = Column(Text)
    query = Column(Text)  # JSON字符串
    auth = Column(Text)  # JSON字符串
    request_name = Column(String(255), unique=True)
    is_deleted = Column(Integer, default=0)

class RequestHistory(Base):
    """请求执行历史表"""
    __tablename__ = 'request_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_info_id = Column(Integer)  # 不使用外键
    timestamp = Column(String(50), nullable=False)
    url = Column(Text)
    method = Column(String(10))
    auth = Column(Text)  # JSON字符串
    request_name = Column(String(255))
    request_headers = Column(Text)  # JSON字符串
    request_body = Column(Text)
    response_status = Column(Integer)
    response_headers = Column(Text)  # JSON字符串
    response_body = Column(Text)
    response_time = Column(Integer)
    execution_status = Column(String(50))
    execution_message = Column(Text)
    execution_details = Column(Text)  # JSON字符串
    query = Column(Text)  # JSON字符串
    pre_request_results = Column(Text)  # JSON字符串
    username = Column(String(100))

class User(Base):
    """用户表"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default='user')
    created_at = Column(String(50), nullable=False)
    last_login = Column(String(50))

class Project(Base):
    """项目表"""
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    created_by = Column(Integer, nullable=False)  # 不使用外键
    created_at = Column(String(50), nullable=False)
    updated_at = Column(String(50))
    status = Column(String(20), nullable=False, default='active')

class UserProjectPermission(Base):
    """用户项目权限表"""
    __tablename__ = 'user_project_permissions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)  # 不使用外键
    project_id = Column(Integer, nullable=False)  # 不使用外键
    permission_level = Column(String(20), nullable=False, default='read')
    granted_by = Column(Integer, nullable=False)  # 不使用外键
    granted_at = Column(String(50), nullable=False)

# UserRequestRelation 表已删除，不再需要

class ProjectRequestRelation(Base):
    """项目与请求关系表"""
    __tablename__ = 'project_request_relations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, nullable=False)  # 不使用外键
    request_info_id = Column(Integer, nullable=False)  # 不使用外键
    created_at = Column(String(50), nullable=False)

class AdvancedConfig(Base):
    """高级配置表"""
    __tablename__ = 'advanced_config'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, nullable=False)  # 不使用外键
    request_info_id = Column(Integer)  # 不使用外键
    is_global = Column(Integer, default=0)
    body_info = Column(Text)
    query_info = Column(Text)
    created_at = Column(String(50), default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    updated_at = Column(String(50), default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    request_name = Column(String(255))
    private_request_id = Column(Integer)
    host = Column(String(255))

class ProjectEnv(Base):
    """项目环境配置表"""
    __tablename__ = 'project_env'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer)  # 不使用外键
    env = Column(Text)
    created_at = Column(String(50), default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    updated_at = Column(String(50), default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))