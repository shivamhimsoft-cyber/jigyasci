# routes\auth_routes.py
import re  # Add this import at the top
from flask import (
    Blueprint, render_template, redirect, url_for, flash,
    request, session, jsonify, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import random, string, time

from models import User, Register, Profile
from forms import LoginForm, RegistrationForm
from extensions import db, mail
from flask_mail import Message as MailMessage

auth_bp = Blueprint('auth', __name__)

# Allowed domains for PI and Student users
ALLOWED_DOMAINS = ['.ac.in', '.edu.in', '.gov.in', '.nic.in', '.res.in', 
                  '.ernet.in', '.isro.gov.in', '.drdo.in', '.nptel.iitm.ac.in', 
                  '.swayam.gov.in', 'gmail.com']

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # 👇 Redirect to correct dashboard based on user_type if already logged in
        if current_user.user_type == 'Admin':
            return redirect(url_for('admin.admin_dashboard'))
        elif current_user.user_type == 'PI':
            return redirect(url_for('pi.faculty_dashboard'))
        elif current_user.user_type == 'Student':
            return redirect(url_for('student.student_profile'))
        elif current_user.user_type == 'Industry':
            return redirect(url_for('industry.industry_dashboard'))
        elif current_user.user_type == 'Vendor':
            return redirect(url_for('vendor.vendor_dashboard'))
        else:
            return redirect(url_for('index'))
            

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not check_password_hash(user.password_hash, form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)
        flash('Login successful!', 'success')

        # Redirect to respective dashboard based on user type
        if user.user_type == 'Admin':
            return redirect(url_for('admin.admin_dashboard'))
        elif user.user_type == 'PI':
            return redirect(url_for('pi.faculty_dashboard'))
        elif user.user_type == 'Student':
            return redirect(url_for('student.student_profile'))
        elif user.user_type == 'Industry':
            return redirect(url_for('industry.industry_dashboard'))
        elif user.user_type == 'Vendor':
            return redirect(url_for('vendor.vendor_dashboard'))
        else:
            return redirect(url_for('index'))

    return render_template('auth/login.html', title='Sign In', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect('/')   # goes directly to http://127.0.0.1:5000/




@auth_bp.route('/check_email', methods=['POST'])
def check_email():
    data = request.get_json()
    email = data.get('email')
    
    user = User.query.filter_by(email=email).first()
    return jsonify({'exists': user is not None})

# ------------------ SEND OTP ------------------
@auth_bp.route('/send_otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data.get('email')
    user_type = data.get('user_type')
    
    # Validate email domain for PI and Student
    if user_type in ['PI', 'Student']:
        domain_valid = any(email.endswith(allowed) for allowed in ALLOWED_DOMAINS)
        if not domain_valid:
            return jsonify({'error': 'Invalid email domain for ' + user_type + ' user'}), 400
    
    # Check if email already exists
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    otp = ''.join(random.choices(string.digits, k=6))
    session['otp'] = otp
    session['otp_email'] = email
    session['otp_time'] = (datetime.utcnow() + timedelta(minutes=5)).timestamp()

    try:
        # Create HTML email template
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Your Verification Code - jigyasci</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    margin: 0;
                    padding: 0;
                    background-color: #f9f9f9;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 30px 20px;
                    text-align: center;
                    color: white;
                }}
                .logo {{
                    font-size: 28px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                .content {{
                    padding: 30px;
                }}
                .otp-container {{
                    background-color: #f8f9fa;
                    border-radius: 6px;
                    padding: 20px;
                    text-align: center;
                    margin: 25px 0;
                    border: 1px dashed #dee2e6;
                }}
                .otp-code {{
                    font-size: 32px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    color: #495057;
                    margin: 15px 0;
                    font-family: 'Courier New', monospace;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #6c757d;
                    border-top: 1px solid #e9ecef;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #667eea;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    font-weight: 500;
                    margin-top: 20px;
                }}
                .info-box {{
                    background-color: #e8f4fd;
                    border-left: 4px solid #2196F3;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">JIGYASCI</div>
                    <h2>Email Verification</h2>
                </div>
                
                <div class="content">
                    <p>Hello,</p>
                    <p>Thank you for choosing jigyasci - the Research Collaboration Platform. To complete your registration, please use the following verification code:</p>
                    
                    <div class="otp-container">
                        <p>Your verification code is:</p>
                        <div class="otp-code">{otp}</div>
                        <p>This code will expire in <strong>5 minutes</strong>.</p>
                    </div>
                    
                    <div class="info-box">
                        <strong>Security Tip:</strong> Never share this code with anyone. jigyasci will never ask you for your verification code.
                    </div>
                    
                    <p>If you didn't request this code, please ignore this email or contact our support team if you have concerns.</p>
                    
                    <p>Welcome to our community of researchers and innovators!</p>
                    
                    <p>Best regards,<br>The jigyasci Team</p>
                </div>
                
                <div class="footer">
                    <p>© {datetime.now().year} jigyasci Research Collaboration Platform. All rights reserved.</p>
                    <p>This is an automated message, please do not reply to this email.</p>
                    <p>If you need assistance, please contact our support team at support@jigyasci.com</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version for email clients that don't support HTML
        text_content = f"""
        jigyasci - Email Verification
        
        Hello,
        
        Thank you for choosing jigyasci - the Research Collaboration Platform. 
        To complete your registration, please use the following verification code:
        
        Your verification code: {otp}
        This code will expire in 5 minutes.
        
        Security Tip: Never share this code with anyone. jigyasci will never ask you for your verification code.
        
        If you didn't request this code, please ignore this email.
        
        Best regards,
        The jigyasci Team
        
        © {datetime.now().year} jigyasci Research Collaboration Platform. All rights reserved.
        This is an automated message, please do not reply to this email.
        """
        
        msg = MailMessage(
            subject='Your jigyasci Verification Code',
            sender=('jigyasci Support', current_app.config['MAIL_USERNAME']),
            recipients=[email]
        )
        
        # Add both HTML and plain text versions
        msg.body = text_content
        msg.html = html_content
        
        mail.send(msg)
        return jsonify({'message': 'OTP sent successfully'})
    except Exception as e:
        current_app.logger.error(f"Failed to send OTP email: {str(e)}")
        return jsonify({'error': 'Failed to send verification code. Please try again.'}), 500
# ------------------ VERIFY OTP ------------------
@auth_bp.route('/verify_otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    entered_otp = data.get('otp')
    entered_email = data.get('email')

    if (session.get('otp') == entered_otp and session.get('otp_email') == entered_email 
        and datetime.utcnow().timestamp() < session.get('otp_time', 0)):
        session['otp_verified'] = True
        session.pop('otp', None)
        session.pop('otp_email', None)
        session.pop('otp_time', None)
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Invalid or expired OTP'})

# ------------------ REGISTER ------------------
# routes\auth_routes.py
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        # Get user_type from either the form or request (for disabled fields)
        user_type = form.user_type.data or request.form.get('user_type')
        email = form.email.data
        password = form.password.data
        password2 = form.password2.data
        agree_terms = form.agree_terms.data

        if not session.get('otp_verified'):
            flash('❌ Please verify your email before registering.', 'danger')
            return render_template('auth/register.html', form=form)

        # Validate email domain for PI and Student
        if user_type in ['PI', 'Student']:
            domain_valid = any(email.endswith(allowed) for allowed in ALLOWED_DOMAINS)
            if not domain_valid:
                flash('❌ Invalid email domain for ' + user_type + ' user', 'danger')
                return render_template('auth/register.html', form=form)

        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('❌ Email already registered.', 'danger')
            return render_template('auth/register.html', form=form)

        try:
            hashed_password = generate_password_hash(password)
            user = User(email=email, user_type=user_type, password_hash=hashed_password,
                        created_at=datetime.utcnow(), last_login=datetime.utcnow(),
                        verification_status='Verified', account_status='Active')
            db.session.add(user)
            db.session.flush()

            profile = Profile(user_id=user.id, profile_type=user_type, profile_completeness=0,
                              visibility_settings='Public', last_updated=datetime.utcnow())
            db.session.add(profile)
            db.session.flush()

            register_entry = Register(email=email, user_type=user_type, user_id=user.id,
                                      profile_id=profile.id, verified=True,
                                      password_hash=hashed_password, created_at=datetime.utcnow())
            db.session.add(register_entry)

            db.session.commit()
            session.pop('otp_verified', None)
            flash('✅ Registration successful! You may log in now.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('❌ Something went wrong. Please try again.', 'danger')
            print("Registration error:", e)
            return render_template('auth/register.html', form=form)

    # Prefill form if session email exists
    if 'register_email' in session:
        form.email.data = session['register_email']
    if 'register_user_type' in session:
        form.user_type.data = session['register_user_type']

    return render_template('auth/register.html', form=form)




# @auth_bp.route('/debug/check-db')
# def debug_check_db():
#     """Check database connection and content"""
#     try:
#         # Test connection
#         db.session.execute('SELECT 1')
        
#         # Get counts
#         user_count = User.query.count()
#         profile_count = Profile.query.count()
#         register_count = Register.query.count()
        
#         # Get latest entries
#         latest_user = User.query.order_by(User.id.desc()).first()
#         latest_profile = Profile.query.order_by(Profile.id.desc()).first()
#         latest_register = Register.query.order_by(Register.id.desc()).first()
        
#         return jsonify({
#             'success': True,
#             'counts': {
#                 'users': user_count,
#                 'profiles': profile_count,
#                 'registers': register_count
#             },
#             'latest': {
#                 'user': {
#                     'id': latest_user.id if latest_user else None,
#                     'email': latest_user.email if latest_user else None
#                 } if latest_user else None,
#                 'profile': {
#                     'id': latest_profile.id if latest_profile else None,
#                     'user_id': latest_profile.user_id if latest_profile else None
#                 } if latest_profile else None,
#                 'register': {
#                     'id': latest_register.id if latest_register else None,
#                     'email': latest_register.email if latest_register else None
#                 } if latest_register else None
#             }
#         })
#     except Exception as e:
#         return jsonify({
#             'success': False,
#             'error': str(e)
#         }), 500

# @auth_bp.route('/debug/test-insert')
# def debug_test_insert():
#     """Test database insert operation"""
#     try:
#         from werkzeug.security import generate_password_hash
#         from datetime import datetime
        
#         test_email = f"test_{datetime.now().strftime('%H%M%S_%f')}@test.com"
        
#         # Create user
#         user = User(
#             email=test_email,
#             user_type='Student',
#             password_hash=generate_password_hash('test1234'),
#             verification_status='Verified',
#             account_status='Active'
#         )
#         db.session.add(user)
#         db.session.flush()
        
#         # Create profile
#         profile = Profile(
#             user_id=user.id,
#             profile_type='Student'
#         )
#         db.session.add(profile)
#         db.session.flush()   # <-- yaha flush karna zaroori hai
        
#         # Create register entry
#         register = Register(
#             user_id=user.id,
#             profile_id=profile.id,
#             email=test_email,
#             user_type='Student',
#             password_hash=generate_password_hash('test123'),
#             verified=True,
#         )
#         db.session.add(register)
        
#         db.session.commit()
        
#         return jsonify({
#             'success': True,
#             'message': f'Test data inserted successfully: {test_email}',
#             'user_id': user.id,
#             'profile_id': profile.id,
#             'register_id': register.id
#         })
        
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({
#             'success': False,
#             'error': str(e)
#         }), 500