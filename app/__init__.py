import os
import click
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///videos.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads"),
        MAX_CONTENT_LENGTH=2 * 1024 * 1024 * 1024,
    )

    os.makedirs(os.path.abspath(app.config["UPLOAD_FOLDER"]), exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .views.auth import bp as auth_bp
    from .views.video import bp as video_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(video_bp)

    # 自动初始化数据库
    with app.app_context():
        db.create_all()
        # 如果没有管理员，创建默认管理员
        if User.query.filter_by(is_admin=True).count() == 0:
            default_admin = User(
                username="admin",
                password_hash=generate_password_hash("admin123"),
                is_admin=True
            )
            db.session.add(default_admin)
            db.session.commit()
            print("✓ 数据库已初始化")
            print("✓ 默认管理员已创建: username=admin, password=admin123")
            print("⚠ 请登录后立即修改密码！")
        
        # 启动时清理孤立文件
        from .views.video import cleanup_orphaned_files
        cleanup_orphaned_files()

    @app.cli.command("init-db")
    def init_db_command():
        with app.app_context():
            db.create_all()
        click.echo("initialized")

    @app.cli.command("create-admin")
    @click.option("--username", required=True)
    @click.option("--password", required=True)
    def create_admin(username, password):
        from .models import User
        with app.app_context():
            existing = User.query.filter_by(username=username).first()
            if existing:
                click.echo("exists")
                return
            user = User(username=username, password_hash=generate_password_hash(password), is_admin=True)
            db.session.add(user)
            db.session.commit()
            click.echo("created")
    
    @app.cli.command("cleanup-files")
    def cleanup_files_command():
        """清理没有数据库记录的孤立文件"""
        from .views.video import cleanup_orphaned_files
        with app.app_context():
            cleanup_orphaned_files()
            click.echo("cleanup completed")

    return app