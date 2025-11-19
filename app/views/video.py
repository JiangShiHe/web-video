import os
from flask import Blueprint, render_template, request, redirect, url_for, current_app, abort, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from ..models import Video
from .. import db

bp = Blueprint("video", __name__)

def allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"mp4", "webm", "ogg", "mov", "mkv"}

@bp.route("/")
def index():
    public_videos = Video.query.filter_by(is_public=True).order_by(Video.id.desc()).all()
    return render_template("index.html", videos=public_videos)

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
            return render_template("upload.html", error="请输入标题并选择文件")
        if not allowed(file.filename):
            return render_template("upload.html", error="不支持的文件类型")
        filename = secure_filename(file.filename)
        base, ext = os.path.splitext(filename)
        unique = f"{base}_{os.urandom(8).hex()}{ext}"
        folder = os.path.abspath(current_app.config["UPLOAD_FOLDER"])
        os.makedirs(folder, exist_ok=True)
        filepath = os.path.join(folder, unique)
        file.save(filepath)
        v = Video(title=title, filename=unique, is_public=is_public, uploader_id=current_user.id)
        db.session.add(v)
        db.session.commit()
        return redirect(url_for("video.detail", vid=v.id))
    return render_template("upload.html")