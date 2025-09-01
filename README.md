<div align="center">

# 🚀 XAPI-Tester

**一个功能强大的 API 测试和管理平台**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-1.4+-red.svg)](https://www.sqlalchemy.org/)

一个功能完整的 API 测试工具平台，支持多用户、项目管理、请求历史记录和高级配置功能。基于 Flask + SQLite 构建，提供直观的 Web 界面进行 API 测试和管理。

</div>

---

## ✨ 功能特点

### 🔐 用户认证与权限管理
- 用户注册、登录系统（支持注册开关控制）
- JWT Token 认证
- LDAP 集成支持
- 基于角色的权限控制（管理员/普通用户）
- 项目级权限控制（读取、写入、管理员权限）

### 📋 项目管理
- 多项目支持
- 项目成员管理
- 项目环境配置
- 项目请求分组管理

### 🚀 API 测试功能
- 支持 GET、POST、PUT、DELETE、PATCH 等 HTTP 方法
- 自定义请求头和认证信息
- 支持 JSON、Form-data、Raw 等请求体格式
- 实时响应展示（状态码、响应头、响应体）
- 响应数据格式化（JSON、XML、HTML）
- 请求响应时间统计

### 📊 数据管理
- 请求历史记录
- 基于项目的请求管理
- 请求复制和删除功能
- 数据导入导出

### ⚙️ 高级配置
- 环境变量管理
- 全局配置设置
- 请求模板管理
- 响应式界面设计

## 🛠️ 技术栈

- **后端**: Python 3.x + Flask
- **数据库**: SQLite（支持 Alembic 数据库迁移）
- **前端**: HTML5 + CSS3 + JavaScript + Layui
- **认证**: JWT + LDAP
- **其他**: Flask-CORS、Requests、PyJWT

## 📦 安装部署

### 环境要求

- Python 3.7+
- pip 包管理器

### 快速开始

1. **克隆项目**
```bash
git clone <repository-url>
cd trae_demo
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置文件**

编辑 `config.json` 文件，配置数据库、LDAP 和 JWT 设置：

```json
{
  "ldap_config": {
    "server": "your-ldap-server",
    "port": 389,
    "use_ssl": false,
    "base_dn": "dc=example,dc=com"
  },
  "database": {
    "type": "sqlite",
    "path": "api_tester.db"
  },
  "jwt_config": {
    "secret_key": "your-secret-key"
  },
  "user_config": {
    "allow_registration": true,
    "admin_users": ["admin", "administrator"],
    "default_role": "user"
  }
}
```

4. **初始化数据库**
```bash
python -c "from db_orm import init_db; init_db()"
```

5. **启动服务**
```bash
python main.py
```

服务将在 http://localhost:5000 启动。
注册页面 http://localhost:5000/register.html

### 数据库迁移

项目使用 Alembic 进行数据库版本管理：

```bash
# 生成迁移文件
alembic revision --autogenerate -m "描述信息"

# 执行迁移
alembic upgrade head

# 查看迁移历史
alembic history
```

## 🎯 使用指南

### 首次使用

1. **注册账户**
   - 访问 http://localhost:5000
   - 点击「注册」创建新账户
   - 或使用 LDAP 账户登录（如已配置）

2. **创建项目**
   - 登录后点击「新建项目」
   - 填写项目名称和描述
   - 设置项目成员权限

3. **配置环境**
   - 进入项目设置
   - 添加环境变量（如 API_BASE_URL、TOKEN 等）
   - 配置全局请求头

### API 测试流程

1. **创建请求**
   - 选择 HTTP 方法
   - 输入请求 URL
   - 设置请求头和认证信息
   - 配置请求体（支持 JSON、Form 等格式）

2. **发送请求**
   - 点击「发送」按钮
   - 查看实时响应结果
   - 检查响应时间和状态码

3. **保存和管理**
   - 保存常用请求为模板
   - 查看请求历史记录
   - 导出测试数据

## 📁 项目结构

```
trae_demo/
├── api/                    # API 路由模块
│   ├── api_server.py      # 主要 API 接口
│   ├── api_user.py        # 用户管理 API
│   ├── api_project.py     # 项目管理 API
│   ├── api_project_env.py # 项目环境配置 API
│   └── api_advanced_config.py # 高级配置 API
├── html/                   # 前端页面
│   ├── api_tester.html    # 主测试界面
│   ├── login.html         # 登录页面
│   ├── register.html      # 注册页面
│   ├── project_list.html  # 项目列表
│   ├── project_config.html # 项目配置
│   ├── advanced_config_content.html # 高级配置
│   └── ...
├── js/                     # 静态资源
│   ├── layui@2.11.5/      # UI 框架
│   ├── xapi/              # 自定义 JS
│   └── xapi_tool.js       # 主要工具脚本
├── model/                  # 数据模型
│   └── models.py          # SQLAlchemy 模型定义
├── migrations/             # 数据库迁移文件
├── util/                   # 工具模块
│   ├── ldap_auth_middleware.py # LDAP 认证中间件
│   ├── xapi_replace.py    # API 替换工具
│   └── xapi_res.py        # API 响应工具
├── config.json            # 配置文件
├── main.py                # 应用入口
├── auth.py                # 认证模块
├── db_orm.py              # 数据库操作
├── api_routes.py          # API 路由注册
├── api_view.py            # 视图路由
└── requirements.txt       # 依赖列表
```

## 🔧 配置说明

### 数据库配置

- **SQLite**: 默认使用 SQLite，适合开发和小型部署
- **MySQL**: 可配置 MySQL 数据库（需修改 config.json）

### 🚀 高级配置使用说明

#### 前置请求配置

高级配置功能允许您设置前置请求，用于在主请求执行前获取必要的数据（如认证令牌）。目前系统支持前置请求功能，可以通过特定的变量引用格式在后续请求中使用前置请求的结果。

#### 变量引用格式

前置请求的结果可以通过以下格式在主请求的 body、query 参数和 header 中引用：

```
$xapi.custom.{请求ID}.{响应部分}.{字段路径}
```

**格式说明：**
- `$xapi.custom/global`：固定前缀，标识这是一个自定义变量引用/全局变量
- `{请求ID}`：前置请求的唯一标识符（如：13）
- `{响应部分}`：指定要引用的响应部分
  - `body`：响应体内容
  - `header`：响应头信息
- `{字段路径}`：具体的字段路径，支持嵌套对象访问

#### 使用示例

**1. 引用响应体中的 token 字段：**
```
$xapi.custom.13.body.token
```

**2. 引用嵌套对象中的字段：**
```
$xapi.custom.13.body.data.access_token
$xapi.custom.13.body.user.id
```

**3. 引用响应头信息：**
```
$xapi.custom.13.header.Authorization
$xapi.custom.13.header.Set-Cookie
```

#### 配置步骤

1. **创建前置请求**：在高级配置中设置前置请求，获取所需的认证信息或其他数据
2. **记录请求ID**：每个前置请求都有唯一的ID标识
3. **配置变量引用**：在主请求中使用 `$xapi.custom.{ID}.{部分}.{字段}` 格式引用前置请求的结果
4. **测试验证**：确保变量引用正确，前置请求能够成功执行并传递数据

#### 注意事项

- 前置请求必须在主请求之前成功执行
- 变量引用的字段路径必须存在于前置请求的响应中
- 支持多层嵌套对象的字段访问
- 变量替换在请求执行时动态进行

### LDAP 集成

支持企业 LDAP 认证，配置 `ldap_config` 部分：

- `server`: LDAP 服务器地址
- `port`: LDAP 端口（通常 389 或 636）
- `use_ssl`: 是否使用 SSL
- `base_dn`: 基础 DN

### JWT 认证

- `secret_key`: JWT 签名密钥（生产环境请使用强密钥）
- Token 有效期：24 小时

### 用户配置

- `allow_registration`: 是否允许用户注册（true/false）
- `admin_users`: 管理员用户名列表
- `default_role`: 新用户默认角色（user/admin）

## 🚀 部署建议

### 生产环境

1. **使用 WSGI 服务器**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

2. **配置反向代理**

使用 Nginx 作为反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. **安全配置**
   - 修改默认 JWT 密钥
   - 配置 HTTPS
   - 设置防火墙规则
   - 定期备份数据库

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📝 更新日志

### v2.0.0 (最新)

**架构优化**
- 移除了用户请求关系管理功能，简化架构
- 删除 `user_request_relations` 表和相关 API
- 移除 `admin_requests.html` 权限管理页面
- 优化项目管理模式，专注于基于项目的请求管理

**功能增强**
- 新增用户注册开关控制功能
- 优化用户角色分配逻辑
- 改进项目权限管理
- 增强配置文件管理

**技术改进**
- 代码结构优化，提高可维护性
- 数据库模型简化
- API 接口精简
- 前端界面优化

## 🆘 支持与反馈

如遇到问题或有功能建议，请：

1. 查看 [Issues](../../issues) 页面
2. 创建新的 Issue
3. 联系项目维护者

---

**快速链接**: [安装指南](#-安装部署) | [使用指南](#-使用指南) | [API 文档](#) | [更新日志](#-更新日志)