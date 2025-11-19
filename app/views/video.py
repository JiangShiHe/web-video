import os
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, current_app, abort, send_file, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from ..models import Video, ShareToken
from .. import db

bp = Blueprint("video", __name__)

def allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"mp4", "webm", "ogg", "mov", "mkv"}

def cleanup_orphaned_files():
    """清理没有数据库记录的孤立文件"""
    try:
        folder = os.path.abspath(current_app.config["UPLOAD_FOLDER"])
        if not os.path.exists(folder):
            return
        
        # 获取所有数据库中的文件名
        db_filenames = {v.filename for v in Video.query.all()}
        
        # 遍历上传目录
        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename)
            # 跳过目录和.gitkeep文件
            if os.path.isdir(filepath) or filename == ".gitkeep":
                continue
            
            # 如果文件不在数据库中，删除它
            if filename not in db_filenames:
                try:
                    os.remove(filepath)
                    print(f"✓ 已清理孤立文件: {filename}")
                except Exception as e:
                    print(f"✗ 清理文件失败 {filename}: {e}")
    except Exception as e:
        print(f"✗ 清理孤立文件时出错: {e}")

@bp.route("/")
def index():
    if current_user.is_authenticated and current_user.is_admin:
        # 管理员可以看到所有视频
        videos = Video.query.order_by(Video.id.desc()).all()
    else:
        # 普通用户只能看到公开视频
        videos = Video.query.filter_by(is_public=True).order_by(Video.id.desc()).all()
    return render_template("index.html", videos=videos)

@bp.route("/videos/<int:vid>")
def detail(vid):
    v = Video.query.get_or_404(vid)
    if not v.is_public:
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
    return render_template("video_detail.html", video=v)

@bp.route("/stream/<int:vid>")
def stream(vid):
    v = Video.query.get_or_404(vid)
    if not v.is_public:
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
    path = os.path.abspath(os.path.join(current_app.config["UPLOAD_FOLDER"], v.filename))
    if not os.path.isfile(path):
        abort(404)
    
    # 添加缓存控制头
    response = send_file(path, conditional=True)
    response.headers['Cache-Control'] = 'public, max-age=31536000'  # 缓存1年
    response.headers['Accept-Ranges'] = 'bytes'
    return response

@bp.route("/admin/upload", methods=["GET", "POST"])
@login_required
def upload():
    if not current_user.is_admin:
        abort(403)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        is_public = request.form.get("is_public") == "on"
        file = request.files.get("file")
        
        if not title or not file or file.filename == "":
            return jsonify({"success": False, "error": "请输入标题并选择文件"})
        if not allowed(file.filename):
            return jsonify({"success": False, "error": "不支持的文件类型"})
        
        filename = secure_filename(file.filename)
        base, ext = os.path.splitext(filename)
        unique = f"{base}_{os.urandom(8).hex()}{ext}"
        folder = os.path.abspath(current_app.config["UPLOAD_FOLDER"])
        os.makedirs(folder, exist_ok=True)
        filepath = os.path.join(folder, unique)
        
        try:
            file.save(filepath)
            v = Video(title=title, filename=unique, is_public=is_public, uploader_id=current_user.id)
            db.session.add(v)
            db.session.commit()
            
            # 上传成功后清理孤立文件
            cleanup_orphaned_files()
            
            return jsonify({"success": True, "redirect": url_for("video.detail", vid=v.id)})
        except Exception as e:
            # 如果保存失败，删除已上传的文件
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({"success": False, "error": f"上传失败: {str(e)}"})
    
    return render_template("upload.html")

@bp.route("/admin/videos/<int:vid>/edit", methods=["GET", "POST"])
@login_required
def edit(vid):
    if not current_user.is_admin:
        abort(403)
    v = Video.query.get_or_404(vid)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        is_public = request.form.get("is_public") == "on"
        if not title:
            return render_template("edit.html", video=v, error="标题不能为空")
        v.title = title
        v.is_public = is_public
        db.session.commit()
        return redirect(url_for("video.detail", vid=v.id))
    return render_template("edit.html", video=v)

@bp.route("/admin/videos/<int:vid>/delete", methods=["POST"])
@login_required
def delete(vid):
    if not current_user.is_admin:
        abort(403)
    v = Video.query.get_or_404(vid)
    # 删除文件
    filepath = os.path.abspath(os.path.join(current_app.config["UPLOAD_FOLDER"], v.filename))
    if os.path.isfile(filepath):
        os.remove(filepath)
    # 删除数据库记录
    db.session.delete(v)
    db.session.commit()
    return redirect(url_for("video.index"))

# ============================================
# 分享功能
# ============================================

@bp.route("/admin/videos/<int:vid>/share", methods=["POST"])
@login_required
def create_share(vid):
    """生成分享链接"""
    if not current_user.is_admin:
        return jsonify({"success": False, "error": "权限不足"}), 403
    
    video = Video.query.get_or_404(vid)
    
    # 获取参数
    expires_hours = request.json.get("expires_hours")  # 过期时间（小时），None表示永久
    max_views = request.json.get("max_views")  # 最大访问次数，None表示无限制
    
    # 生成随机令牌
    token = secrets.token_urlsafe(32)
    
    # 计算过期时间
    expires_at = None
    if expires_hours:
        expires_at = datetime.utcnow() + timedelta(hours=int(expires_hours))
    
    # 创建分享令牌
    share = ShareToken(
        video_id=video.id,
        token=token,
        expires_at=expires_at,
        max_views=max_views,
        created_by=current_user.id
    )
    db.session.add(share)
    db.session.commit()
    
    # 生成分享链接
    share_url = url_for("video.share_view", token=token, _external=True)
    
    return jsonify({
        "success": True,
        "share_url": share_url,
        "token": token,
        "expires_at": expires_at.isoformat() if expires_at else None
    })

@bp.route("/share/<token>")
def share_view(token):
    """通过分享链接访问视频"""
    share = ShareToken.query.filter_by(token=token).first_or_404()
    
    # 检查令牌是否有效
    if not share.is_valid():
        abort(403, "分享链接已失效")
    
    # 增加访问次数
    share.increment_view()
    
    # 显示视频
    video = share.video
    return render_template("video_detail.html", video=video, is_shared=True)

@bp.route("/admin/videos/<int:vid>/shares")
@login_required
def list_shares(vid):
    """查看视频的所有分享链接"""
    if not current_user.is_admin:
        abort(403)
    
    video = Video.query.get_or_404(vid)
    shares = ShareToken.query.filter_by(video_id=vid).order_by(ShareToken.created_at.desc()).all()
    
    return render_template("shares.html", video=video, shares=shares)

@bp.route("/admin/shares/<int:share_id>/toggle", methods=["POST"])
@login_required
def toggle_share(share_id):
    """启用/禁用分享链接"""
    if not current_user.is_admin:
        return jsonify({"success": False, "error": "权限不足"}), 403
    
    share = ShareToken.query.get_or_404(share_id)
    share.is_active = not share.is_active
    db.session.commit()
    
    return jsonify({"success": True, "is_active": share.is_active})

@bp.route("/admin/shares/<int:share_id>/delete", methods=["POST"])
@login_required
def delete_share(share_id):
    """删除分享链接"""
    if not current_user.is_admin:
        return jsonify({"success": False, "error": "权限不足"}), 403
    
    share = ShareToken.query.get_or_404(share_id)
    db.session.delete(share)
    db.session.commit()
    
    return jsonify({"success": True})