# 服务器部署指南

## 问题：SQLAlchemy版本兼容性错误

如果遇到 `AttributeError: module 'sqlalchemy' has no attribute '__all__'` 错误，按以下步骤解决：

### 方案1：完全重装依赖（推荐）

```bash
cd /www/wwwroot/web-video

# 1. 拉取最新代码
git pull

# 2. 卸载所有相关包
pip uninstall -y Flask Flask-Login Flask-SQLAlchemy SQLAlchemy Werkzeug

# 3. 清理pip缓存
pip cache purge

# 4. 重新安装（使用指定版本）
pip install --no-cache-dir -r requirements.txt

# 5. 验证安装
pip list | grep -E "Flask|SQLAlchemy"
```

### 方案2：使用虚拟环境（最佳实践）

```bash
cd /www/wwwroot/web-video

# 1. 创建虚拟环境
python3 -m venv venv

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 4. 运行应用
python run.py
```

### 方案3：降级Python版本

如果Python 3.13仍有问题，建议使用Python 3.11或3.12：

```bash
# 使用pyenv或系统包管理器安装Python 3.11
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 生产环境部署

### 使用Gunicorn

```bash
# 安装Gunicorn
pip install gunicorn

# 启动应用（4个worker进程）
gunicorn -w 4 -b 0.0.0.0:9003 run:app

# 后台运行
nohup gunicorn -w 4 -b 0.0.0.0:9003 run:app > gunicorn.log 2>&1 &
```

### 使用Supervisor管理进程

创建配置文件 `/etc/supervisor/conf.d/web-video.conf`：

```ini
[program:web-video]
directory=/www/wwwroot/web-video
command=/www/wwwroot/web-video/venv/bin/gunicorn -w 4 -b 0.0.0.0:9003 run:app
user=www
autostart=true
autorestart=true
stderr_logfile=/var/log/web-video.err.log
stdout_logfile=/var/log/web-video.out.log
```

启动服务：
```bash
supervisorctl reread
supervisorctl update
supervisorctl start web-video
```

### Nginx反向代理配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 2G;

    location / {
        proxy_pass http://127.0.0.1:9003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 视频流优化
    location /stream/ {
        proxy_pass http://127.0.0.1:9003;
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Range $http_range;
        proxy_set_header If-Range $http_if_range;
    }
}
```

## 默认管理员账号

- 用户名：`admin`
- 密码：`admin123`

⚠️ **重要：登录后请立即修改密码！**

## 环境变量配置

生产环境建议设置：

```bash
export SECRET_KEY="your-random-secret-key-here"
export DATABASE_URL="sqlite:///videos.db"  # 或使用PostgreSQL
```

## 故障排查

### 查看依赖版本
```bash
pip list | grep -E "Flask|SQLAlchemy"
```

### 测试导入
```bash
python -c "from flask_sqlalchemy import SQLAlchemy; print('OK')"
```

### 查看Python版本
```bash
python --version
```
