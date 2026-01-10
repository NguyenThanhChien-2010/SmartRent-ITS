from flask import Flask
from flask_login import LoginManager
from config import config
from app.models import db, User
from app.utils.firebase_client import init_firebase

login_manager = LoginManager()

def create_app(config_name='development'):
    """Factory function để tạo Flask app"""
    app = Flask(__name__, 
                template_folder='views',
                static_folder='static')
    
    # Load config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Vui lòng đăng nhập để truy cập trang này.'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.controllers.main_controller import main_bp
    from app.controllers.auth_controller import auth_bp
    from app.controllers.vehicle_controller import vehicle_bp
    from app.controllers.trip_controller import trip_bp
    from app.controllers.payment_controller import payment_bp
    from app.controllers.admin_controller import admin_bp
    from app.controllers.emergency_controller import emergency_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(vehicle_bp)
    app.register_blueprint(trip_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(emergency_bp)
    
    # Create tables
    with app.app_context():
        # Initialize Firebase (optional)
        init_firebase(app)
        db.create_all()
    
    return app
