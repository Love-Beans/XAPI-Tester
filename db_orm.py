from sqlalchemy import create_engine, and_, or_, desc
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import IntegrityError
import json
import os
from datetime import datetime
from log_base import MyLog
from config import config
from model.models import (
    Base, RequestInfo, RequestHistory, User, Project, 
    UserProjectPermission, ProjectRequestRelation,
    AdvancedConfig, ProjectEnv
)

log = MyLog().my_logger()

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = None
        self.Session = None
        self.session = None
        self._init_database()
    
    def _init_database(self):
        """初始化数据库连接"""
        try:
            # 从配置获取数据库连接信息
            db_config = config.get_database_config()
            db_type = db_config.get('type', 'sqlite')
            
            if db_type == 'sqlite':
                db_path = db_config.get('path', 'api_tester.db')
                database_url = f'sqlite:///{db_path}'
            elif db_type == 'mysql':
                host = db_config.get('host', 'localhost')
                port = db_config.get('port', 3306)
                username = db_config.get('username', 'root')
                password = db_config.get('password', '')
                database = db_config.get('database', 'api_tester')
                database_url = f'mysql+pymysql://{username}:{password}@{host}:{port}/{database}'
            elif db_type == 'postgresql':
                host = db_config.get('host', 'localhost')
                port = db_config.get('port', 5432)
                username = db_config.get('username', 'postgres')
                password = db_config.get('password', '')
                database = db_config.get('database', 'api_tester')
                database_url = f'postgresql://{username}:{password}@{host}:{port}/{database}'
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
            
            self.engine = create_engine(database_url, echo=False)
            self.Session = scoped_session(sessionmaker(bind=self.engine))
            
            # 创建所有表
            Base.metadata.create_all(self.engine)
            
            log.info(f"Database initialized successfully with {db_type}")
            
        except Exception as e:
            log.error(f"Database initialization failed: {e}")
            raise
    
    def get_session(self):
        """获取数据库会话"""
        return self.Session()
    
    def close_session(self, session):
        """关闭数据库会话"""
        if session:
            session.close()

# 全局数据库管理器实例
db_manager = DatabaseManager()

def get_db_session():
    """获取数据库会话的便捷函数"""
    return db_manager.get_session()

def init_db():
    """初始化数据库（兼容原有接口）"""
    # SQLAlchemy 在 DatabaseManager 初始化时已经创建了所有表
    log.info("Database tables initialized")

def save_or_update_request_info(url, method, headers, body, query, auth=None, request_name=None, request_info_id=None):
    """保存或更新请求信息到request_info表"""
    session = get_db_session()
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if request_info_id:
            # 更新现有记录
            request_info = session.query(RequestInfo).filter_by(id=request_info_id).first()
            if request_info:
                request_info.timestamp = timestamp
                request_info.url = url
                request_info.method = method
                request_info.headers = json.dumps(headers) if headers else None
                request_info.body = body
                request_info.query = json.dumps(query) if query else None
                request_info.auth = json.dumps(auth) if auth else None
                request_info.request_name = request_name
                info_id = request_info_id
                log.info(f"Updating request info with ID: {request_info_id}")
            else:
                return None
        else:
            # 插入新记录
            request_info = RequestInfo(
                timestamp=timestamp,
                url=url,
                method=method,
                headers=json.dumps(headers) if headers else None,
                body=body,
                query=json.dumps(query) if query else None,
                auth=json.dumps(auth) if auth else None,
                request_name=request_name,
                is_deleted=0
            )
            session.add(request_info)
            session.flush()  # 获取ID
            info_id = request_info.id
            log.info(f"Inserting new request name: {request_name}")
        
        session.commit()
        return info_id
        
    except Exception as e:
        session.rollback()
        log.error(f"Error saving request info: {e}")
        return None
    finally:
        db_manager.close_session(session)

def get_all_projects():
    """获取所有项目（管理员专用）"""
    session = get_db_session()
    try:
        projects = session.query(Project).order_by(desc(Project.created_at)).all()
        
        result = []
        for project in projects:
            # 查找创建者用户名
            creator = session.query(User).filter_by(id=project.created_by).first()
            result.append({
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'created_at': project.created_at,
                'created_by': project.created_by,
                'created_username': creator.username if creator else 'Unknown'
            })
        
        return result
        
    except Exception as e:
        log.error(f"Error getting all projects: {e}")
        return []
    finally:
        db_manager.close_session(session)

def add_project_request_relation(project_id, request_info_id):
    """添加项目与请求的关系"""
    session = get_db_session()
    try:
        # 检查关系是否已存在
        existing = session.query(ProjectRequestRelation).filter_by(
            project_id=project_id, 
            request_info_id=request_info_id
        ).first()
        
        if not existing:
            relation = ProjectRequestRelation(
                project_id=project_id,
                request_info_id=request_info_id,
                created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            session.add(relation)
            session.commit()
        
        return True
        
    except Exception as e:
        session.rollback()
        log.error(f"添加项目请求关系失败: {e}")
        return False
    finally:
        db_manager.close_session(session)

def remove_project_request_relation(project_id, request_info_id):
    """删除项目与请求的关系"""
    session = get_db_session()
    try:
        relation = session.query(ProjectRequestRelation).filter_by(
            project_id=project_id,
            request_info_id=request_info_id
        ).first()
        
        if relation:
            session.delete(relation)
            session.commit()
        
        return True
        
    except Exception as e:
        session.rollback()
        log.error(f"删除项目请求关系失败: {e}")
        return False
    finally:
        db_manager.close_session(session)

def get_request_ids_by_project(project_id):
    """根据项目ID查询相关的请求ID列表"""
    session = get_db_session()
    try:
        relations = session.query(ProjectRequestRelation).filter_by(
            project_id=project_id
        ).order_by(desc(ProjectRequestRelation.created_at)).all()
        
        return [relation.request_info_id for relation in relations]
        
    except Exception as e:
        log.error(f"查询项目请求关系失败: {e}")
        return []
    finally:
        db_manager.close_session(session)

def get_requests_by_project_id(project_id):
    """根据项目ID获取请求列表"""
    session = get_db_session()
    try:
        results = session.query(RequestInfo).join(
            ProjectRequestRelation,
            RequestInfo.id == ProjectRequestRelation.request_info_id
        ).filter(
            ProjectRequestRelation.project_id == project_id,
            RequestInfo.is_deleted == 0
        ).order_by(desc(RequestInfo.timestamp)).all()
        
        requests = []
        for request_info in results:
            request_dict = {
                'id': request_info.id,
                'timestamp': request_info.timestamp,
                'url': request_info.url,
                'method': request_info.method,
                'headers': request_info.headers,
                'body': request_info.body,
                'query': request_info.query,
                'auth': request_info.auth,
                'request_name': request_info.request_name
            }
            requests.append(request_dict)
        
        return requests
        
    except Exception as e:
        log.error(f"查询项目请求详情失败: {e}")
        return []
    finally:
        db_manager.close_session(session)

def check_request_in_project(project_id, request_info_id):
    """检查请求是否属于某个项目"""
    session = get_db_session()
    try:
        relation = session.query(ProjectRequestRelation).filter_by(
            project_id=project_id,
            request_info_id=request_info_id
        ).first()
        
        return relation is not None
        
    except Exception as e:
        log.error(f"检查请求项目关系失败: {e}")
        return False
    finally:
        db_manager.close_session(session)

def save_to_history(request_info_id, response_status, response_headers, response_body, response_time, 
                   url=None, method=None, auth=None, request_name=None, query=None, 
                   request_headers=None, request_body=None, execution_status=None, 
                   execution_message=None, execution_details=None, pre_request_results=None, username=None):
    """保存请求执行历史到request_history表"""
    session = get_db_session()
    try:
        history = RequestHistory(
            request_info_id=request_info_id,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            url=url,
            method=method,
            auth=json.dumps(auth) if auth else None,
            request_name=request_name,
            request_headers=json.dumps(request_headers) if request_headers else None,
            request_body=request_body,
            response_status=response_status,
            response_headers=json.dumps(response_headers) if response_headers else None,
            response_body=response_body,
            response_time=response_time,
            query=json.dumps(query) if query else None,
            execution_status=execution_status,
            execution_message=execution_message,
            execution_details=json.dumps(execution_details) if execution_details else None,
            pre_request_results=json.dumps(pre_request_results) if pre_request_results else None,
            username=username
        )
        
        session.add(history)
        session.commit()
        
        return history.id
        
    except Exception as e:
        session.rollback()
        log.error(f"Error saving to history: {e}")
        return None
    finally:
        db_manager.close_session(session)

def get_request_info_list():
    """获取所有请求信息（用于左侧显示）"""
    session = get_db_session()
    try:
        requests = session.query(RequestInfo).filter(
            RequestInfo.is_deleted == 0
        ).order_by(desc(RequestInfo.id)).all()
        
        request_list = []
        for request_info in requests:
            # 解析存储的JSON字符串
            try:
                headers = json.loads(request_info.headers) if request_info.headers else {}
            except:
                headers = {}
                
            try:
                query = json.loads(request_info.query) if request_info.query else {}
            except:
                query = {}
                
            try:
                request_auth = json.loads(request_info.auth) if request_info.auth else {}
            except:
                request_auth = {}
            
            request_list.append({
                'id': request_info.id,
                'timestamp': request_info.timestamp,
                'url': request_info.url,
                'method': request_info.method,
                'headers': headers,
                'body': request_info.body,
                'query': query,
                'auth': request_auth,
                'request_name': request_info.request_name
            })
        
        return request_list
        
    except Exception as e:
        log.error(f"Error getting request info list: {e}")
        return []
    finally:
        db_manager.close_session(session)

def get_history_by_request_info_id(request_info_id):
    """根据请求信息ID获取历史记录"""
    session = get_db_session()
    try:
        histories = session.query(RequestHistory).filter_by(
            request_info_id=request_info_id
        ).order_by(desc(RequestHistory.id)).all()
        
        return _format_history_data(histories)
        
    except Exception as e:
        log.error(f"Error getting history by request info id: {e}")
        return []
    finally:
        db_manager.close_session(session)

def get_history_by_request_info_id_with_permission(request_info_id, user_id, user_role):
    """根据请求信息ID和用户权限获取历史记录"""
    session = get_db_session()
    try:
        # 管理员可以查看所有记录
        if user_role == 'admin':
            histories = session.query(RequestHistory).filter_by(
                request_info_id=request_info_id
            ).order_by(desc(RequestHistory.id)).all()
        else:
            # 检查用户是否是项目Owner
            # 首先获取请求所属的项目
            project_relation = session.query(ProjectRequestRelation).filter_by(
                request_info_id=request_info_id
            ).first()
            
            if project_relation:
                # 检查用户对该项目的权限
                permission = check_user_project_permission(user_id, project_relation.project_id)
                if permission == 'owner':
                    # 项目Owner可以查看所有记录
                    histories = session.query(RequestHistory).filter_by(
                        request_info_id=request_info_id
                    ).order_by(desc(RequestHistory.id)).all()
                else:
                    # 其他权限用户只能查看自己的记录
                    user = session.query(User).filter_by(id=user_id).first()
                    if user:
                        histories = session.query(RequestHistory).filter_by(
                            request_info_id=request_info_id,
                            username=user.username
                        ).order_by(desc(RequestHistory.id)).all()
                    else:
                        histories = []
            else:
                # 如果请求不属于任何项目，只能查看自己的记录
                user = session.query(User).filter_by(id=user_id).first()
                if user:
                    histories = session.query(RequestHistory).filter_by(
                        request_info_id=request_info_id,
                        username=user.username
                    ).order_by(desc(RequestHistory.id)).all()
                else:
                    histories = []
        
        return _format_history_data(histories)
        
    except Exception as e:
        log.error(f"Error getting history by request info id with permission: {e}")
        return []
    finally:
        db_manager.close_session(session)

def _format_history_data(histories):
    """格式化历史记录数据"""
    history = []
    for row in histories:
        # 解析存储的JSON字符串
        try:
            response_headers = json.loads(row.response_headers) if row.response_headers else {}
        except:
            response_headers = {}
            
        try:
            response_body = json.loads(row.response_body) if row.response_body else {}
        except:
            response_body = row.response_body
            
        try:
            auth = json.loads(row.auth) if row.auth else {}
        except:
            auth = {}
            
        try:
            query = json.loads(row.query) if row.query else {}
        except:
            query = {}
            
        try:
            request_headers = json.loads(row.request_headers) if row.request_headers else {}
        except:
            request_headers = {}
            
        try:
            request_body = row.request_body if row.request_body else ''
        except:
            request_body = ''
            
        try:
            execution_details = json.loads(row.execution_details) if row.execution_details else None
        except:
            execution_details = None
            
        try:
            pre_request_results = json.loads(row.pre_request_results) if row.pre_request_results else None
        except:
            pre_request_results = None
        
        # 构建执行状态对象
        execution_status = None
        if row.execution_status:
            execution_status = {
                'id': row.id,
                'timestamp': row.timestamp,
                'status': row.execution_status,
                'message': row.execution_message,
                'details': execution_details
            }
        
        history.append({
            'id': row.id,
            'timestamp': row.timestamp,
            'request_info_id': row.request_info_id,
            'username': row.username,
            'pre_request_results': pre_request_results,
            'request': {
                'url': row.url,
                'method': row.method,
                'headers': request_headers,
                'auth': auth,
                'body': request_body,
                'query': query,
                'name': row.request_name
            },
            'response': {
                'status': row.response_status,
                'headers': response_headers,
                'body': response_body
            },
            'responseTime': row.response_time,
            'executionStatus': execution_status,
            'queryParams': query
        })
    
    return history

def get_request_info_by_id(request_info_id):
    """根据ID获取请求信息"""
    session = get_db_session()
    try:
        request_info = session.query(RequestInfo).filter_by(
            id=request_info_id,
            is_deleted=0
        ).first()
        
        if not request_info:
            return None
            
        # 解析存储的JSON字符串
        try:
            headers = json.loads(request_info.headers) if request_info.headers else {}
        except:
            headers = {}
            
        try:
            query = json.loads(request_info.query) if request_info.query else {}
        except:
            query = {}
            
        try:
            auth = json.loads(request_info.auth) if request_info.auth else {}
        except:
            auth = {}
        
        return {
            'id': request_info.id,
            'timestamp': request_info.timestamp,
            'url': request_info.url,
            'method': request_info.method,
            'headers': headers,
            'body': request_info.body,
            'query': query,
            'auth': auth,
            'request_name': request_info.request_name
        }
        
    except Exception as e:
        log.error(f"Error getting request info by id: {e}")
        return None
    finally:
        db_manager.close_session(session)

# ==================== 用户管理相关函数 ====================

def create_user(username, password, role='user'):
    """创建新用户"""
    session = get_db_session()
    try:
        user = User(
            username=username,
            password=password,
            role=role,
            created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        session.add(user)
        session.commit()
        return user.id
    except IntegrityError:
        session.rollback()
        return None
    except Exception as e:
        session.rollback()
        log.error(f"Error creating user: {e}")
        return None
    finally:
        db_manager.close_session(session)

def verify_user(username, password):
    """验证用户登录"""
    session = get_db_session()
    try:
        user = session.query(User).filter_by(username=username, password=password).first()
        if user:
            return {
                'id': user.id,
                'username': user.username,
                'role': user.role
            }
        return None
    except Exception as e:
        log.error(f"Error verifying user: {e}")
        return None
    finally:
        db_manager.close_session(session)

def get_user_by_id(user_id):
    """根据ID获取用户信息"""
    session = get_db_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            return {
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'created_at': user.created_at,
                'last_login': user.last_login
            }
        return None
    except Exception as e:
        log.error(f"Error getting user by id: {e}")
        return None
    finally:
        db_manager.close_session(session)

def get_user_by_username(username):
    """根据用户名获取用户信息"""
    session = get_db_session()
    try:
        user = session.query(User).filter_by(username=username).first()
        if user:
            return {
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'created_at': user.created_at,
                'last_login': user.last_login
            }
        return None
    except Exception as e:
        log.error(f"Error getting user by username: {e}")
        return None
    finally:
        db_manager.close_session(session)

def update_user_last_login(timestamp, user_id):
    """更新用户最后登录时间"""
    session = get_db_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            user.last_login = timestamp
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        log.error(f"Error updating user last login: {e}")
        return False
    finally:
        db_manager.close_session(session)

# ==================== 项目管理相关函数 ====================

def create_project(name, description, created_by):
    """创建新项目"""
    session = get_db_session()
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        project = Project(
            name=name,
            description=description,
            created_by=created_by,
            created_at=timestamp,
            updated_at=timestamp
        )
        session.add(project)
        session.flush()  # 获取项目ID
        
        # 自动给创建者分配所有者权限
        permission = UserProjectPermission(
            user_id=created_by,
            project_id=project.id,
            permission_level='owner',
            granted_by=created_by,
            granted_at=timestamp
        )
        session.add(permission)
        session.commit()
        
        return project.id
    except Exception as e:
        session.rollback()
        log.error(f"Error creating project: {e}")
        return None
    finally:
        db_manager.close_session(session)

def get_user_projects(user_id):
    """获取用户有权限的项目列表"""
    session = get_db_session()
    try:
        results = session.query(Project, UserProjectPermission, User).join(
            UserProjectPermission, Project.id == UserProjectPermission.project_id
        ).join(
            User, Project.created_by == User.id
        ).filter(
            UserProjectPermission.user_id == user_id,
            Project.status == 'active'
        ).order_by(desc(Project.updated_at)).all()
        
        projects = []
        for project, permission, creator in results:
            projects.append({
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'created_at': project.created_at,
                'updated_at': project.updated_at,
                'status': project.status,
                'permission_level': permission.permission_level,
                'created_username': creator.username
            })
        
        return projects
    except Exception as e:
        log.error(f"Error getting user projects: {e}")
        return []
    finally:
        db_manager.close_session(session)

def get_project_by_id(project_id):
    """获取项目详情"""
    session = get_db_session()
    try:
        project = session.query(Project).filter_by(id=project_id).first()
        if project:
            creator = session.query(User).filter_by(id=project.created_by).first()
            return {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'created_by': project.created_by,
                'created_at': project.created_at,
                'updated_at': project.updated_at,
                'status': project.status,
                'created_username': creator.username if creator else 'Unknown'
            }
        return None
    except Exception as e:
        log.error(f"Error getting project by id: {e}")
        return None
    finally:
        db_manager.close_session(session)

def check_user_project_permission(user_id, project_id):
    """检查用户对项目的权限"""
    session = get_db_session()
    try:
        permission = session.query(UserProjectPermission).filter_by(
            user_id=user_id,
            project_id=project_id
        ).first()
        
        if permission:
            return permission.permission_level
        return None
    except Exception as e:
        log.error(f"Error checking user project permission: {e}")
        return None
    finally:
        db_manager.close_session(session)

def get_project_members(project_id):
    """获取项目成员列表"""
    session = get_db_session()
    try:
        results = session.query(User, UserProjectPermission).join(
            UserProjectPermission, User.id == UserProjectPermission.user_id
        ).filter(
            UserProjectPermission.project_id == project_id
        ).all()
        
        members = []
        for user, permission in results:
            members.append({
                'user_id': user.id,
                'username': user.username,
                'role': user.role,
                'permission_level': permission.permission_level,
                'granted_at': permission.granted_at
            })
        
        return members
    except Exception as e:
        log.error(f"Error getting project members: {e}")
        return []
    finally:
        db_manager.close_session(session)

def remove_project_member(user_id, project_id):
    """移除项目成员"""
    session = get_db_session()
    try:
        permission = session.query(UserProjectPermission).filter_by(
            user_id=user_id,
            project_id=project_id
        ).first()
        
        if permission:
            session.delete(permission)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        log.error(f"Error removing project member: {e}")
        return False
    finally:
        db_manager.close_session(session)

def grant_project_permission(user_id, project_id, permission_level, granted_by):
    """授予项目权限"""
    session = get_db_session()
    try:
        # 检查权限是否已存在
        existing = session.query(UserProjectPermission).filter_by(
            user_id=user_id,
            project_id=project_id
        ).first()
        
        if existing:
            existing.permission_level = permission_level
            existing.granted_by = granted_by
            existing.granted_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            permission = UserProjectPermission(
                user_id=user_id,
                project_id=project_id,
                permission_level=permission_level,
                granted_by=granted_by,
                granted_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            session.add(permission)
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        log.error(f"Error granting project permission: {e}")
        return False
    finally:
        db_manager.close_session(session)

def get_project_requests(project_id):
    """获取项目的请求列表"""
    return get_requests_by_project_id(project_id)

# ==================== 用户请求关系相关函数已删除 ====================
# UserRequestRelation 表和相关功能已移除

def get_all_request_list():
    """获取所有请求列表"""
    return get_request_info_list()

def get_all_users_list():
    """获取所有用户列表"""
    session = get_db_session()
    try:
        users = session.query(User).order_by(desc(User.created_at)).all()
        
        user_list = []
        for user in users:
            user_list.append({
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'created_at': user.created_at,
                'last_login': user.last_login
            })
        
        return user_list
    except Exception as e:
        log.error(f"Error getting all users list: {e}")
        return []
    finally:
        db_manager.close_session(session)

# 以下函数已删除，因为 UserRequestRelation 表已移除：
# - get_all_requests_with_users()
# - remove_user_request_relation()
# - check_user_request_permission()

def check_user_request_permission(user_id, request_info_id, user_role):
    """检查用户对请求的权限（简化版本）"""
    # 管理员有所有权限
    if user_role == 'admin':
        return True
    
    # 普通用户暂时没有特定权限检查，可根据需要扩展
    return False

# ==================== 高级配置相关函数 ====================

def save_advanced_config(project_id, request_info_id, is_global, body_info, query_info, request_name=None, private_request_id=None, host=None):
    """保存高级配置"""
    session = get_db_session()
    try:
        config = AdvancedConfig(
            project_id=project_id,
            request_info_id=request_info_id,
            is_global=is_global,
            body_info=body_info,
            query_info=query_info,
            request_name=request_name,
            private_request_id=private_request_id,
            host=host,
            created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            updated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        session.add(config)
        session.commit()
        return config.id
    except Exception as e:
        session.rollback()
        log.error(f"Error saving advanced config: {e}")
        return None
    finally:
        db_manager.close_session(session)

def get_advanced_config(project_id, is_global=None, private_request_id=None):
    """获取高级配置"""
    session = get_db_session()
    try:
        query = session.query(AdvancedConfig).filter_by(project_id=project_id)
        
        if is_global is not None:
            query = query.filter_by(is_global=is_global)
        
        if private_request_id is not None and is_global == 0:
            query = query.filter_by(private_request_id=private_request_id)
        
        configs = query.order_by(desc(AdvancedConfig.created_at)).all()
        
        result = []
        for config in configs:
            result.append({
                'id': config.id,
                'project_id': config.project_id,
                'request_info_id': config.request_info_id,
                'is_global': config.is_global,
                'body_info': config.body_info,
                'query_info': config.query_info,
                'created_at': config.created_at,
                'updated_at': config.updated_at,
                'request_name': config.request_name,
                'private_request_id': config.private_request_id,
                'host': config.host
            })
        
        return result
    except Exception as e:
        log.error(f"Error getting advanced config: {e}")
        return []
    finally:
        db_manager.close_session(session)

def update_advanced_config(config_id, project_id, request_info_id, is_global, body_info, query_info, request_name=None, private_request_id=None, host=None):
    """更新高级配置"""
    session = get_db_session()
    try:
        config = session.query(AdvancedConfig).filter_by(id=config_id).first()
        if config:
            config.project_id = project_id
            config.request_info_id = request_info_id
            config.is_global = is_global
            config.body_info = body_info
            config.query_info = query_info
            config.request_name = request_name
            config.private_request_id = private_request_id
            config.host = host
            config.updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        log.error(f"Error updating advanced config: {e}")
        return False
    finally:
        db_manager.close_session(session)

def delete_advanced_config(config_id):
    """删除高级配置"""
    session = get_db_session()
    try:
        config = session.query(AdvancedConfig).filter_by(id=config_id).first()
        if config:
            session.delete(config)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        log.error(f"Error deleting advanced config: {e}")
        return False
    finally:
        db_manager.close_session(session)

# ==================== 项目环境配置相关函数 ====================

def get_project_env(project_id):
    """获取项目环境配置"""
    session = get_db_session()
    try:
        env = session.query(ProjectEnv).filter_by(project_id=project_id).first()
        if env:
            return {
                'id': env.id,
                'project_id': env.project_id,
                'env': env.env,
                'created_at': env.created_at,
                'updated_at': env.updated_at
            }
        return None
    except Exception as e:
        log.error(f"Error getting project env: {e}")
        return None
    finally:
        db_manager.close_session(session)

def save_project_env(project_id, env_json):
    """保存项目环境配置"""
    session = get_db_session()
    try:
        # 检查是否已存在
        existing = session.query(ProjectEnv).filter_by(project_id=project_id).first()
        
        if existing:
            existing.env = env_json
            existing.updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            env = ProjectEnv(
                project_id=project_id,
                env=env_json,
                created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            updated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            session.add(env)
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        log.error(f"Error saving project env: {e}")
        return False
    finally:
        db_manager.close_session(session)

def delete_project_env(project_id):
    """删除项目环境配置"""
    session = get_db_session()
    try:
        env = session.query(ProjectEnv).filter_by(project_id=project_id).first()
        if env:
            session.delete(env)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        log.error(f"Error deleting project env: {e}")
        return False
    finally:
        db_manager.close_session(session)

# ==================== 请求复制和删除相关函数 ====================

def copy_request_info(request_id, project_id):
    """复制请求信息"""
    session = get_db_session()
    try:
        # 获取原始请求信息
        original = session.query(RequestInfo).filter_by(
            id=request_id,
            is_deleted=0
        ).first()
        if not original:
            return None
        
        # 创建新的请求信息
        new_request = RequestInfo(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            url=original.url,
            method=original.method,
            headers=original.headers,
            body=original.body,
            query=original.query,
            auth=original.auth,
            request_name=f"{original.request_name}_copy" if original.request_name else None,
            is_deleted=0
        )
        session.add(new_request)
        session.flush()  # 获取新ID
        
        # 添加项目关联
        if project_id:
            relation = ProjectRequestRelation(
                project_id=project_id,
                request_info_id=new_request.id,
                created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            session.add(relation)
        
        session.commit()
        return new_request.id
    except Exception as e:
        session.rollback()
        log.error(f"Error copying request info: {e}")
        return None
    finally:
        db_manager.close_session(session)

def delete_request_info(request_id, project_id):
    """软删除请求信息"""
    session = get_db_session()
    try:
        # 删除项目关联
        if project_id:
            relation = session.query(ProjectRequestRelation).filter_by(
                project_id=project_id,
                request_info_id=request_id
            ).first()
            if relation:
                session.delete(relation)
        
        # 检查是否还有其他项目关联
        other_relations = session.query(ProjectRequestRelation).filter_by(
            request_info_id=request_id
        ).count()
        
        # 如果没有其他关联，软删除请求信息
        if other_relations != 0:
            remove_project_request_relation(project_id, request_id)
        request_info = session.query(RequestInfo).filter_by(
            id=request_id,
            is_deleted=0
        ).first()
        if request_info:
            request_info.is_deleted = 1
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        log.error(f"Error deleting request info: {e}")
        return False
    finally:
        db_manager.close_session(session)