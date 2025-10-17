# Updated routes/auth_routes.py (with Scientist instead of Faculty, and Google user_type selection)
import re
from flask import (
    Blueprint, render_template, redirect, url_for, flash,
    request, session, jsonify, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import random, string, time

from models import User, Register, Profile, UserType # Note: ALLOWED_DOMAINS moved to models or keep here
from forms import LoginForm, RegistrationForm
from extensions import db, mail
from flask_mail import Message as MailMessage

auth_bp = Blueprint('auth', __name__)

# Allowed domains for Scientist and Student users (can move to models.py if preferred)
ALLOWED_DOMAINS = ['.ac.in', '.edu.in', '.gov.in', '.nic.in', '.res.in', 
                  '.ernet.in', '.isro.gov.in', '.drdo.in', '.nptel.iitm.ac.in', 
                  '.swayam.gov.in', 'gmail.com', 'yopmail.com']

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirect logic (updated for Scientist)
        if current_user.user_type == 'Admin':
            return redirect(url_for('admin.admin_dashboard'))
        elif current_user.user_type == 'Scientist':
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

        # NEW: Check account status before login
        if user.account_status != 'Active':
            flash('Your account is not active. Please wait for admin verification if you are a Scientist.', 'warning')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)
        user.last_login = datetime.utcnow()  # Update last_login
        db.session.commit()
        flash('Login successful!', 'success')

        # Redirect logic (updated for Scientist)
        if user.user_type == 'Admin':
            return redirect(url_for('admin.admin_dashboard'))
        elif user.user_type == 'Scientist':
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

# Google login routes (updated for Scientist and user_type selection)
@auth_bp.route('/login-google')
def login_google():
    from app import google
    redirect_uri = url_for('auth.google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


# Updated routes/auth_routes.py (fix userinfo URL)
@auth_bp.route('/google-callback')
def google_callback():
    from app import google
    try:
        token = google.authorize_access_token()
        # Use full userinfo endpoint URL
        resp = google.get('https://www.googleapis.com/oauth2/v2/userinfo', token=token)
        user_info = resp.json()
        
        email = user_info.get('email')
        name = user_info.get('name')
        
        if not email:
            flash('Google login failed: No email provided', 'error')
            return redirect(url_for('auth.login'))
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if user:
            # Update last_login
            user.last_login = datetime.utcnow()
            # Ensure Scientist status is pending if newly detected as Scientist
            if user.user_type == 'Scientist' and user.account_status == 'Active':
                user.account_status = 'Inactive'
                user.verification_status = 'Pending'
                db.session.commit()
                current_app.logger.info(f"Updated existing Scientist user {email} to pending status.")
            db.session.commit()
            flash('Login successful!', 'success')
            
            # NEW: Check account status before login
            if user.account_status != 'Active':
                flash('Your account is not active. Please wait for admin verification if you are a Scientist.', 'warning')
                current_app.logger.info(f"Redirecting inactive user {email} to login.")
                return redirect(url_for('auth.login'))
            
            login_user(user)
            
            # Redirect based on user_type (updated for Scientist)
            if user.user_type == 'Admin':
                return redirect(url_for('admin.admin_dashboard'))
            elif user.user_type == 'Scientist':
                return redirect(url_for('pi.faculty_dashboard'))
            elif user.user_type == 'Student':
                return redirect(url_for('student.student_profile'))
            elif user.user_type == 'Industry':
                return redirect(url_for('industry.industry_dashboard'))
            elif user.user_type == 'Vendor':
                return redirect(url_for('vendor.vendor_dashboard'))
            else:
                return redirect(url_for('index'))
        else:
            # New user: Store in session and redirect to user_type selection
            session['google_email'] = email
            session['google_name'] = name
            flash('Please select your user type to complete signup.', 'info')
            current_app.logger.info(f"New Google user {email}, redirecting to user_type select.")
            return redirect(url_for('auth.google_user_type_select'))
            
    except Exception as e:
        current_app.logger.error(f"Google callback error for {email if 'email' in locals() else 'unknown'}: {str(e)}")
        flash(f'Google login failed: {str(e)}', 'error')
        return redirect(url_for('auth.login'))




# NEW: Route for Google user_type selection (updated to pass dynamic user_types)
@auth_bp.route('/google_user_type_select', methods=['GET', 'POST'])
def google_user_type_select():
    if 'google_email' not in session:
        flash('Invalid session. Please try Google login again.', 'error')
        return redirect(url_for('auth.login'))

    email = session['google_email']
    name = session['google_name']

    # Query active user types dynamically
    user_types = UserType.query.filter_by(status='Active').all()

    if request.method == 'POST':
        user_type = request.form.get('user_type')
        if not user_type:
            flash('Please select a user type.', 'error')
            return render_template('auth/google_user_type.html', email=email, name=name, user_types=user_types)

        # Check if user now exists (in case manual reg meanwhile)
        user = User.query.filter_by(email=email).first()
        if user:
            # Login existing user
            if user.account_status != 'Active':
                flash('Your account is not active. Please wait for admin verification if you are a Scientist.', 'warning')
                session.pop('google_email', None)
                session.pop('google_name', None)
                return redirect(url_for('auth.login'))

            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash('Login successful!', 'success')

            # Redirect based on user_type (updated for Scientist)
            if user.user_type == 'Admin':
                return redirect(url_for('admin.admin_dashboard'))
            elif user.user_type == 'Scientist':
                return redirect(url_for('pi.faculty_dashboard'))
            elif user.user_type == 'Student':
                return redirect(url_for('student.student_profile'))
            elif user.user_type == 'Industry':
                return redirect(url_for('industry.industry_dashboard'))
            elif user.user_type == 'Vendor':
                return redirect(url_for('vendor.vendor_dashboard'))
            else:
                return redirect(url_for('index'))

        # Create new user with selected type
        # For Scientist, set pending status
        verification_status = 'Pending' if user_type == 'Scientist' else 'Verified'
        account_status = 'Inactive' if user_type == 'Scientist' else 'Active'
        
        password_hash = generate_password_hash(f'google_{random_string(16)}')
        user = User(
            email=email,
            user_type=user_type,
            password_hash=password_hash,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow(),
            verification_status=verification_status,
            account_status=account_status
        )
        db.session.add(user)
        db.session.flush()
        
        profile = Profile(
            user_id=user.id,
            profile_type=user_type,
            profile_completeness=0,
            visibility_settings='Public',
            last_updated=datetime.utcnow()
        )
        db.session.add(profile)
        db.session.flush()
        
        register_entry = Register(
            email=email,
            user_type=user_type,
            user_id=user.id,
            profile_id=profile.id,
            verified=True,
            password_hash=password_hash,
            created_at=datetime.utcnow()
        )
        db.session.add(register_entry)
        
        db.session.commit()
        
        # Clear session
        session.pop('google_email', None)
        session.pop('google_name', None)
        
        # Check status before login
        if user.account_status != 'Active':
            flash('Your account is pending admin verification. Please wait.', 'warning')
            return redirect(url_for('auth.login'))
        
        login_user(user)
        flash(f'Welcome {name}! Account created successfully.', 'success')
        
        # Redirect based on user_type (updated for Scientist)
        if user_type == 'Admin':
            return redirect(url_for('admin.admin_dashboard'))
        elif user_type == 'Scientist':
            return redirect(url_for('pi.faculty_dashboard'))
        elif user_type == 'Student':
            return redirect(url_for('student.student_profile'))
        elif user_type == 'Industry':
            return redirect(url_for('industry.industry_dashboard'))
        elif user_type == 'Vendor':
            return redirect(url_for('vendor.vendor_dashboard'))
        else:
            return redirect(url_for('index'))

    return render_template('auth/google_user_type.html', email=email, name=name, user_types=user_types)


def random_string(length=16):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect('/')

# check_email, send_otp, verify_otp (updated for Scientist)
@auth_bp.route('/check_email', methods=['POST'])
def check_email():
    data = request.get_json()
    email = data.get('email')
    
    user = User.query.filter_by(email=email).first()
    return jsonify({'exists': user is not None})

@auth_bp.route('/send_otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data.get('email')
    user_type = data.get('user_type')
    
    # Validate email domain for Scientist and Student
    if user_type in ['Scientist', 'Student']:
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
        # HTML and text content (unchanged)
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
        
        msg.body = text_content
        msg.html = html_content
        
        mail.send(msg)
        return jsonify({'message': 'OTP sent successfully'})
    except Exception as e:
        current_app.logger.error(f"Failed to send OTP email: {str(e)}")
        return jsonify({'error': 'Failed to send verification code. Please try again.'}), 500

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

# Updated register route for Scientist pending status
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

        # Validate email domain for Scientist and Student
        if user_type in ['Scientist', 'Student']:
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
            # NEW: Set status based on user_type
            verification_status = 'Pending' if user_type == 'Scientist' else 'Verified'
            account_status = 'Inactive' if user_type == 'Scientist' else 'Active'
            
            user = User(email=email, user_type=user_type, password_hash=hashed_password,
                        created_at=datetime.utcnow(), last_login=datetime.utcnow(),
                        verification_status=verification_status, account_status=account_status)
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

            # Clear any login session to prevent auto-redirect
            logout_user() if current_user.is_authenticated else None
            
            if user_type == 'Scientist':
                flash('✅ Registration successful! Your account is pending admin verification.', 'info')
            else:
                flash('✅ Registration successful! You may log in now.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('❌ Something went wrong. Please try again.', 'danger')
            current_app.logger.error(f"Registration error: {e}")
            return render_template('auth/register.html', form=form)

    # Prefill form if session email exists (unchanged)
    if 'register_email' in session:
        form.email.data = session['register_email']
    if 'register_user_type' in session:
        form.user_type.data = session['register_user_type']

    return render_template('auth/register.html', form=form)

# NEW: Helper function for verification emails (updated for Scientist)
def send_verification_email(email, action):
    if action == 'accepted':
        subject = 'Account Verified - jigyasci'
        html_body = """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Your jigyasci Account Has Been Verified!</h2>
            <p>Congratulations! Your Scientist account has been verified and activated.</p>
            <p>You can now log in and access the full platform.</p>
            <a href="https://www.jigyasci.com/login" style="background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Log In Now</a>
            <p>Best regards,<br>The jigyasci Team</p>
        </div>
        """
        text_body = "Your Scientist account has been verified and activated. Log in at https://www.jigyasci.com/login"
    elif action == 'rejected':
        subject = 'Account Verification Rejected - jigyasci'
        html_body = """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Account Verification Update</h2>
            <p>Unfortunately, your Scientist account verification request has been rejected.</p>
            <p>Please contact support@jigyasci.com for more details.</p>
            <p>Best regards,<br>The jigyasci Team</p>
        </div>
        """
        text_body = "Your Scientist account verification has been rejected. Contact support@jigyasci.com for details."
    
    msg = MailMessage(
        subject=subject,
        sender=('jigyasci Support', current_app.config['MAIL_USERNAME']),
        recipients=[email]
    )
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)