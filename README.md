# 视频管理系统

基于Flask的视频上传和播放平台

## 功能特性

- 用户认证（管理员登录）
- 视频上传（支持mp4, webm, ogg, mov, mkv）
- 视频播放（HTML5原生播放器）
- 倍速播放（0.5x - 2x）
- 公开/私有视频控制
- 视频缓存优化
- 断点续传支持

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
flask --app run init-db
```

### 3. 创建管理员账号

```bash
flask --app run create-admin --username admin --password your_password
```

### 4. 运行应用

```bash
python run.py
```

访问 http://localhost:5000

## 部署建议

### 生产环境配置

1. 设置环境变量：
   - `SECRET_KEY`: 使用强随机密钥
   - `DATABASE_URL`: 使用PostgreSQL等生产数据库

2. 使用WSGI服务器（如Gunicorn）：
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 run:app
```

3. 配置反向代理（Nginx）处理静态文件和视频流

4. 视频文件建议使用对象存储（OSS/S3）

## 技术栈

- Flask 2.2+
- Flask-Login
- Flask-SQLAlchemy
- HTML5 Video API
