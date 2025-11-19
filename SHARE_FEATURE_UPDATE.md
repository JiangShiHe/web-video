# 视频分享功能更新说明

## 功能概述

新增视频分享链接功能，管理员可以为任何视频（包括私有视频）生成分享链接，无需登录即可访问。

## 主要特性

- ✅ 生成随机令牌的分享链接
- ✅ 可设置有效期（1小时、24小时、7天、30天、永久）
- ✅ 可设置访问次数限制（10次、50次、100次、无限制）
- ✅ 可随时禁用/启用分享链接
- ✅ 可删除分享链接
- ✅ 查看分享链接的访问统计
- ✅ 一键复制分享链接

## 数据库更新

新增了 `share_token` 表，用于存储分享令牌信息。

### 自动更新（推荐）

应用会在启动时自动创建新表，无需手动操作。只需重启应用即可：

```bash
# 停止应用
# 拉取最新代码
cd /www/wwwroot/web-video
git pull

# 重启应用（数据库会自动更新）
```

### 手动更新（可选）

如果需要手动创建表，可以使用以下 SQL：

```sql
CREATE TABLE share_token (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    token VARCHAR(64) NOT NULL UNIQUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    max_views INTEGER,
    view_count INTEGER NOT NULL DEFAULT 0,
    created_by INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    FOREIGN KEY (video_id) REFERENCES video(id),
    FOREIGN KEY (created_by) REFERENCES user(id)
);

CREATE INDEX ix_share_token_token ON share_token(token);
```

## 使用方法

### 1. 生成分享链接

1. 以管理员身份登录
2. 打开任意视频详情页
3. 点击"🔗 生成分享链接"按钮
4. 选择有效期和访问次数限制
5. 点击"生成链接"
6. 复制生成的链接分享给他人

### 2. 管理分享链接

1. 在视频详情页点击"📋 管理分享"
2. 查看所有分享链接及其状态
3. 可以禁用/启用或删除分享链接

### 3. 通过分享链接访问

1. 无需登录，直接访问分享链接
2. 自动播放视频
3. 支持倍速播放等所有功能

## 分享链接格式

```
https://your-domain.com/app3/share/abcdef1234567890...
```

## 安全性

- 令牌使用 `secrets.token_urlsafe(32)` 生成，安全性高
- 令牌长度 43 字符，无法被猜测
- 支持过期时间和访问次数限制
- 可随时撤销分享链接

## 注意事项

1. **数据库备份**：更新前建议备份数据库
2. **权限控制**：只有管理员可以生成和管理分享链接
3. **链接安全**：分享链接应谨慎分享，避免泄露
4. **性能影响**：每次访问会增加访问计数，对性能影响极小

## 故障排查

### 问题1：分享链接无法访问

**可能原因：**
- 链接已过期
- 访问次数已达上限
- 链接已被禁用

**解决方法：**
- 检查分享链接管理页面的状态
- 重新生成新的分享链接

### 问题2：数据库表未创建

**解决方法：**
```bash
# 进入应用目录
cd /www/wwwroot/web-video

# 使用 Flask CLI 初始化数据库
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('数据库已更新')"
```

### 问题3：生成分享链接失败

**可能原因：**
- 未以管理员身份登录
- 数据库权限问题

**解决方法：**
- 确认已登录管理员账号
- 检查数据库文件权限

## 更新日志

### v1.1.0 (2025-11-19)

- ✨ 新增视频分享链接功能
- ✨ 支持设置有效期和访问次数限制
- ✨ 新增分享链接管理页面
- ✨ 支持禁用/启用/删除分享链接
- ✨ 新增访问统计功能
- 🎨 优化视频详情页UI
- 📝 完善文档说明

## 技术实现

### 后端

- 新增 `ShareToken` 模型
- 新增分享相关路由：
  - `POST /admin/videos/<vid>/share` - 生成分享链接
  - `GET /share/<token>` - 通过令牌访问视频
  - `GET /admin/videos/<vid>/shares` - 管理分享链接
  - `POST /admin/shares/<id>/toggle` - 启用/禁用
  - `POST /admin/shares/<id>/delete` - 删除

### 前端

- 视频详情页新增分享按钮和对话框
- 新增分享链接管理页面
- 支持一键复制链接
- 响应式设计，支持移动端

## 未来计划

- [ ] 支持密码保护的分享链接
- [ ] 支持批量生成分享链接
- [ ] 支持分享链接的访问日志
- [ ] 支持二维码分享
- [ ] 支持自定义分享链接别名
