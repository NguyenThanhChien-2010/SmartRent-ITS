from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User
from werkzeug.security import generate_password_hash
from app.utils.firebase_client import get_db
from datetime import datetime
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Đăng ký tài khoản mới"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        
        # Validation
        if not all([username, email, password, confirm_password]):
            flash('Vui lòng điền đầy đủ thông tin', 'danger')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Mật khẩu không khớp', 'danger')
            return render_template('auth/register.html')
        
        # Check email format
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('Email không hợp lệ', 'danger')
            return render_template('auth/register.html')
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Email đã được sử dụng', 'danger')
            return render_template('auth/register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Tên đăng nhập đã tồn tại', 'danger')
            return render_template('auth/register.html')
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            role='customer'
        )
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            # Sync to Firestore if enabled
            if current_app.config.get('FIREBASE_ENABLED'):
                fs_db = get_db()
                if fs_db:
                    try:
                        user_data = {
                            'id': new_user.id,
                            'username': new_user.username,
                            'email': new_user.email,
                            'full_name': new_user.full_name,
                            'phone': new_user.phone,
                            'role': new_user.role,
                            'wallet_balance': float(new_user.wallet_balance),
                            'is_active': new_user.is_active,
                            'created_at': datetime.utcnow().isoformat(),
                            'synced_from': 'register'
                        }
                        fs_db.collection('users').document(str(new_user.id)).set(user_data)
                        print(f'[Firebase] User {new_user.email} synced to Firestore')
                    except Exception as firebase_error:
                        print(f'[Firebase] Failed to sync user: {firebase_error}')
            
            flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi: {str(e)}', 'danger')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Đăng nhập"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        if not email or not password:
            flash('Vui lòng nhập email và mật khẩu', 'danger')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Tài khoản đã bị khóa', 'danger')
                return render_template('auth/login.html')
            
            login_user(user, remember=remember)
            flash(f'Chào mừng {user.full_name or user.username}!', 'success')
            
            # Redirect based on role
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            elif user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('main.index'))
        else:
            flash('Email hoặc mật khẩu không đúng', 'danger')
            return render_template('auth/login.html')
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Đăng xuất"""
    logout_user()
    flash('Đăng xuất thành công!', 'success')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile')
@login_required
def profile():
    """Trang thông tin cá nhân"""
    from app.models import Trip, Payment
    
    # Get recent trips (sorted by created_at descending)
    recent_trips = Trip.query.filter_by(user_id=current_user.id)\
        .order_by(Trip.created_at.desc())\
        .limit(5).all()
    
    # Get recent payments (sorted by created_at descending)
    recent_payments = Payment.query.filter_by(user_id=current_user.id)\
        .order_by(Payment.created_at.desc())\
        .limit(10).all()
    
    return render_template('auth/profile.html', 
                         user=current_user,
                         recent_trips=recent_trips,
                         recent_payments=recent_payments)


@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Chỉnh sửa thông tin cá nhân"""
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name')
        current_user.phone = request.form.get('phone')
        
        try:
            db.session.commit()
            flash('Cập nhật thông tin thành công', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi: {str(e)}', 'danger')
    
    return render_template('auth/edit_profile.html', user=current_user)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Đổi mật khẩu"""
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(old_password):
            flash('Mật khẩu cũ không đúng', 'danger')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('Mật khẩu mới không khớp', 'danger')
            return render_template('auth/change_password.html')
        
        current_user.set_password(new_password)
        
        try:
            db.session.commit()
            flash('Đổi mật khẩu thành công', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi: {str(e)}', 'danger')
    
    return render_template('auth/change_password.html')
