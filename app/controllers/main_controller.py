from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Trip, Vehicle, Payment
from sqlalchemy import func
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Trang chủ"""
    if current_user.is_authenticated:
        return render_template('index.html')
    return render_template('landing.html')


@main_bp.route('/about')
def about():
    """Giới thiệu"""
    return render_template('about.html')


@main_bp.route('/contact')
def contact():
    """Liên hệ"""
    return render_template('contact.html')


@main_bp.route('/help')
def help():
    """Trợ giúp"""
    return render_template('help.html')
