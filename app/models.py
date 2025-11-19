from datetime import datetime
from flask_login import UserMixin
from . import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    is_public = db.Column(db.Boolean, default=True)
    uploader_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    uploader = db.relationship("User", backref="videos")

class ShareToken(db.Model):
    """视频分享令牌"""
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey("video.id"), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)  # None表示永久有效
    max_views = db.Column(db.Integer, nullable=True)  # 最大访问次数，None表示无限制
    view_count = db.Column(db.Integer, default=0, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # 是否启用
    
    video = db.relationship("Video", backref="share_tokens")
    creator = db.relationship("User", backref="created_shares")
    
    def is_valid(self):
        """检查令牌是否有效"""
        if not self.is_active:
            return False
        
        # 检查是否过期
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        
        # 检查访问次数
        if self.max_views and self.view_count >= self.max_views:
            return False
        
        return True
    
    def increment_view(self):
        """增加访问次数"""
        self.view_count += 1
        db.session.commit()