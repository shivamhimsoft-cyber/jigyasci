# routes/auth_routes.py
import secrets  
import random
import string
from datetime import datetime, timedelta
from flask import (
    Blueprint, render_template, redirect, url_for, flash,
    request, session, jsonify, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Message as MailMessage

from models import (
    User, Register, Profile, UserType,
    PIProfile, StudentProfile, IndustryProfile, VendorProfile, PasswordResetToken, University, College, CurrentDesignation
)
from forms import LoginForm, RegistrationForm
from extensions import db, mail

auth_bp = Blueprint('auth', __name__)

ALLOWED_DOMAINS = [
    '.ac.in', '.edu.in', '.gov.in', '.nic.in', '.res.in',
    '.ernet.in', '.isro.gov.in', '.drdo.in', '.nptel.iitm.ac.in',
    '.swayam.gov.in', 'gmail.com', 'yopmail.com'
]

# LOGIN
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_by_user_type(current_user)

    form = LoginForm()
    show_pending_modal = session.pop('show_pending_modal', False)

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user or not check_password_hash(user.password_hash, form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))

        if user.account_status != 'Active':
            if user.user_type == 'Scientist':
                session['show_pending_modal'] = True
                flash('Your Scientist account is awaiting admin verification. You will be notified within 24 hours.', 'warning')
            else:
                flash('Your account is not active.', 'warning')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)
        user.last_login = datetime.utcnow()
        db.session.commit()
        flash('Login successful!', 'success')
        return _redirect_by_user_type(user)

    return render_template('auth/login.html', title='Sign In', form=form,
                           show_pending_modal=show_pending_modal)

def _redirect_by_user_type(user):
    mapping = {
        'Admin': url_for('admin.admin_dashboard'),
        'Scientist': url_for('pi.faculty_dashboard'),
        'Student': url_for('student.student_profile'),
        'Industry': url_for('industry.industry_dashboard'),
        'Vendor': url_for('vendor.vendor_dashboard')
    }
    return redirect(mapping.get(user.user_type, url_for('index')))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect('/')

@auth_bp.route('/check_email', methods=['POST'])
def check_email():
    email = request.get_json().get('email')
    exists = User.query.filter_by(email=email).first() is not None
    return jsonify({'exists': exists})

# SEND OTP
@auth_bp.route('/send_otp', methods=['POST'])
def send_otp():
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    user_type = data.get('user_type')

    if not email or not user_type:
        return jsonify({'error': 'Email and user type required'}), 400

    if user_type in ['Scientist', 'Student']:
        if not any(email.lower().endswith(d) for d in ALLOWED_DOMAINS):
            return jsonify({'error': 'Use institutional email'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400

    otp = ''.join(random.choices(string.digits, k=6))
    session['otp'] = otp
    session['otp_email'] = email
    session['otp_time'] = (datetime.utcnow() + timedelta(minutes=10)).timestamp()  # 10 minutes

    try:
        msg = MailMessage("JigyaSci OTP", sender=current_app.config['MAIL_USERNAME'], recipients=[email])
        msg.html = f"""
        <div style="font-family:Arial;max-width:600px;margin:auto;padding:20px;">
            <h3>Your OTP: <strong style="font-size:1.5em;color:#667eea">{otp}</strong></h3>
            <p>Valid for <strong>10 minutes</strong>.</p>
            <p>Do not share this code.</p>
        </div>
        """
        mail.send(msg)
        return jsonify({'message': 'OTP sent'})
    except Exception as e:
        current_app.logger.error(f"OTP failed: {e}")
        return jsonify({'error': 'Failed to send OTP'}), 500

# AUTO REGISTER
def generate_random_password():
    return ''.join(random.choice(string.ascii_letters + string.digits + "!@#$%") for _ in range(10))



def send_account_details_email(email, details):
    login_url = url_for('auth.login', _external=True)
    pending_msg = ""
    if details['user_type'] == 'Scientist':
        pending_msg = "<p class='text-orange-600 font-semibold'>Note: You cannot login yet. Your account is awaiting admin verification. You will receive an email once approved.</p>"

    # Dynamic label for Institution / Industry
    org_label = "Industry Name" if details['user_type'] == 'Industry' else "Institution / Company"
    
    # Phone line (only if provided)
    phone_line = f"<p><strong>Phone:</strong> {details.get('phone') or '—'}</p>" if details.get('phone') else ""

    html = f"""
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:600px;margin:auto;padding:20px;border:1px solid #e2e8f0;border-radius:8px;background:#ffffff;">
        <h2 style="color:#1f2937;margin-bottom:8px;">Welcome to JigyaSci!</h2>
        <p style="color:#4b5563;margin-bottom:16px;">Your account has been created successfully.</p>
        {pending_msg}
        <hr style="border-color:#e5e7eb;margin:20px 0;">
        
        <p style="margin:8px 0;"><strong>User Type:</strong> {details['user_type']}</p>
        <p style="margin:8px 0;"><strong>Full Name:</strong> {details['full_name']}</p>
        <p style="margin:8px 0;"><strong>{org_label}:</strong> {details['organization']}</p>
        <p style="margin:8px 0;"><strong>Designation:</strong> {details['designation']}</p>
        {phone_line}
        <p style="margin:8px 0;"><strong>Email:</strong> {email}</p>
        <p style="margin:8px 0;">
            <strong>Password:</strong> 
            <code style="background:#f3f4f6;padding:4px 8px;border-radius:4px;font-family:monospace;">{details['password']}</code>
        </p>
        
        <hr style="border-color:#e5e7eb;margin:20px 0;">
        <p style="text-align:center;margin:20px 0;">
            <a href="{login_url}" style="background:#667eea;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;font-weight:600;display:inline-block;">
                Go to Login
            </a>
        </p>
        <p style="color:#6b7280;font-size:13px;text-align:center;">
            <small>Change your password after first login for security.</small>
        </p>
    </div>
    """
    
    msg = MailMessage("Your JigyaSci Account", sender=current_app.config['MAIL_USERNAME'], recipients=[email])
    msg.html = html
    mail.send(msg)



@auth_bp.route('/auto_register', methods=['POST'])
def auto_register():
    data = request.get_json(silent=True) or {}
    otp = data.get('otp')
    email = data.get('email')
    user_type = data.get('user_type')
    full_name = data.get('full_name')
    organization_input = data.get('organization')  # str (ID or custom)
    designation_input = data.get('designation')    # str (ID)
    phone = data.get('phone')

    if (session.get('otp') != otp or session.get('otp_email') != email or
        datetime.utcnow().timestamp() > session.get('otp_time', 0)):
        return jsonify({'message': 'Invalid or expired OTP'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already registered'}), 400

    try:
        # Resolve organization name
        if user_type == 'Industry':
            organization_name = organization_input or "Unknown"
        else:
            try:
                org_id = int(organization_input) if organization_input and organization_input != '' else None
            except ValueError:
                org_id = None
            org = University.query.get(org_id) or College.query.get(org_id)
            organization_name = org.name if org else "Unknown"

        # Resolve designation name
        try:
            desig_id = int(designation_input) if designation_input and designation_input != '' else None
        except ValueError:
            desig_id = None
        desig = CurrentDesignation.query.get(desig_id)
        designation_name = desig.name if desig else "Unknown"

        password = generate_random_password()
        hashed = generate_password_hash(password)
        verification_status = 'Pending' if user_type == 'Scientist' else 'Verified'
        account_status = 'Inactive' if user_type == 'Scientist' else 'Active'

        user = User(email=email, user_type=user_type, password_hash=hashed,
                    verification_status=verification_status, account_status=account_status,
                    created_at=datetime.utcnow(), last_login=datetime.utcnow())
        db.session.add(user)
        db.session.flush()

        profile = Profile(user_id=user.id, profile_type=user_type,
                          profile_completeness=20, visibility_settings='Public',
                          last_updated=datetime.utcnow())
        db.session.add(profile)
        db.session.flush()

        if user_type == 'Scientist':
            db.session.add(PIProfile(profile_id=profile.id, name=full_name, affiliation=organization_name,
                                     current_designation=designation_name, current_message='', contact_phone=phone))
        elif user_type == 'Student':
            db.session.add(StudentProfile(profile_id=profile.id, name=full_name, affiliation=organization_name,
                                          contact_email=email, why_me='', contact_phone=phone))
        elif user_type == 'Industry':
            db.session.add(IndustryProfile(profile_id=profile.id, company_name=organization_name,
                                           contact_person=full_name, email=email, contact_phone=phone))
        elif user_type == 'Vendor':
            db.session.add(VendorProfile(profile_id=profile.id, company_name=organization_name,
                                         contact_person=full_name, email=email, contact_phone=phone))

        db.session.add(Register(
            email=email, user_type=user_type, user_id=user.id, profile_id=profile.id,
            verified=True, password_hash=password, created_at=datetime.utcnow()
        ))

        db.session.commit()

        for k in ['otp', 'otp_email', 'otp_time']:
            session.pop(k, None)

        send_account_details_email(email, {
            'user_type': user_type,
            'full_name': full_name,
            'organization': organization_name,
            'designation': designation_name,
            'phone': phone,
            'password': password
        })

        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Auto-register error: {e}")
        return jsonify({'message': 'Registration failed'}), 500


def send_verification_email(user, action, password=None):
    login_url = url_for('auth.login', _external=True)

    # Get name safely
    pi = user.profile.pi_profile if user.profile else None
    name = pi.name if pi else user.email.split('@')[0]

    if action == 'accepted':
        subject = 'Account Verified – You Can Now Login'
        password_line = f"<p><strong>Password:</strong> <code style='background:#f0f0f0;padding:4px 8px;'>{password or '******'}</code></p>"
        html = f"""
        <div style="font-family:Arial;max-width:600px;margin:auto;padding:20px;">
            <h2>Account Verified!</h2>
            <p>Dear {name},</p>
            <p>Your Scientist account has been <strong>approved</strong> and is now active.</p>
            <p>You can now log in using the credentials below:</p>
            <hr>
            <p><strong>Email:</strong> {user.email}</p>
            {password_line}
            <p><a href="{login_url}" style="background:#667eea;color:white;padding:10px 20px;text-decoration:none;border-radius:4px;">Login Now</a></p>
            <p><small>Change password after first login for security.</small></p>
            <p>Best regards,<br>JigyaSci Team</p>
        </div>
        """
    else:  # rejected
        subject = 'Account Verification Rejected'
        html = f"""
        <div style="font-family:Arial;max-width:600px;margin:auto;padding:20px;">
            <h2>Verification Update</h2>
            <p>Dear {name},</p>
            <p>Unfortunately, your Scientist account has been <strong>rejected</strong>.</p>
            <p>Your account has been removed. Contact <a href="mailto:support@jigyasci.com">support@jigyasci.com</a> for details.</p>
            <p>Best regards,<br>JigyaSci Team</p>
        </div>
        """

    msg = MailMessage(subject, sender=current_app.config['MAIL_USERNAME'], recipients=[user.email])
    msg.html = html
    mail.send(msg)



@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    return render_template('auth/register.html', form=form)




@auth_bp.route('/forgot_password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'error': 'Email required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        # Security: Don't reveal if email exists
        return jsonify({'success': True}), 200

    # Generate secure token
    token = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(hours=1)

    # Delete old tokens
    PasswordResetToken.query.filter_by(user_id=user.id).delete()

    reset_token = PasswordResetToken(user_id=user.id, token=token, expires_at=expiry, used=False)
    db.session.add(reset_token)
    db.session.commit()

    # Send email
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    msg = MailMessage(
        "Password Reset Request",
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[email]
    )
    msg.html = f"""
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:600px;margin:auto;padding:20px;background:#f9f9f9;border-radius:8px;">
        <h2 style="color:#333;">Reset Your JigyaSci Password</h2>
        <p style="color:#555;font-size:15px;">You requested a password reset. Click below to set a new password:</p>
        <p style="text-align:center;margin:25px 0;">
            <a href="{reset_url}" style="background:#667eea;color:white;padding:12px 28px;text-decoration:none;border-radius:6px;font-weight:bold;display:inline-block;">
                Reset Password
            </a>
        </p>
        <p style="color:#777;font-size:13px;">This link expires in <strong>1 hour</strong>.</p>
        <p style="color:#999;font-size:12px;">If you didn't request this, please ignore this email.</p>
    </div>
    """
    try:
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Failed to send reset email: {e}")
        return jsonify({'error': 'Failed to send email'}), 500

    return jsonify({'success': True})


@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset = PasswordResetToken.query.filter_by(token=token, used=False).first()
    if not reset or reset.expires_at < datetime.utcnow():
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html', token=token)
        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return render_template('auth/reset_password.html', token=token)

        user = reset.user
        user.password_hash = generate_password_hash(password)
        reset.used = True
        db.session.commit()

        flash('Password updated! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)







# ===================================================================
# GOOGLE + LINKEDIN → FULL REGISTRATION (Same as normal register)
# ===================================================================

@auth_bp.route('/login_google')
def login_google():
    from app import google
    redirect_uri = url_for('auth.oauth_callback', provider='google', _external=True)
    return google.authorize_redirect(redirect_uri)


@auth_bp.route('/login_linkedin')
def login_linkedin():
    client_id = current_app.config['LINKEDIN_CLIENT_ID']
    redirect_uri = url_for('auth.oauth_callback', provider='linkedin', _external=True)
    scope = 'r_liteprofile r_emailaddress'
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state

    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization?"
        f"response_type=code&client_id={client_id}&redirect_uri={redirect_uri}"
        f"&scope={scope}&state={state}"
    )
    return redirect(auth_url)


# Unified OAuth Callback
@auth_bp.route('/oauth_register', methods=['GET', 'POST'])
def oauth_register():
    if 'oauth_email' not in session:
        flash('Session expired. Please try again.', 'danger')
        return redirect(url_for('auth.login'))

    email = session['oauth_email']
    name = session['oauth_name']
    provider = session.get('oauth_provider', 'social')

    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        login_user(existing_user)
        session.pop('oauth_email', None)
        session.pop('oauth_name', None)
        session.pop('oauth_provider', None)
        return redirect(_redirect_by_user_type(existing_user))

    form = RegistrationForm()
    user_types = UserType.query.filter_by(status='Active').all()
    form.user_type.choices = [('', 'Select User Type')] + [(ut.name, ut.name) for ut in user_types]

    if form.validate_on_submit():
        user_type = form.user_type.data
        full_name = form.full_name.data.strip()
        organization = form.organization.data.strip()
        designation = form.designation.data.strip()
        phone = form.phone.data.strip() if form.phone.data else None  # ← Fixed

        # Bio removed → default empty
        bio = ''

        # Scientist → pending
        verification_status = 'Pending' if user_type == 'Scientist' else 'Verified'
        account_status = 'Inactive' if user_type == 'Scientist' else 'Active'

        password = generate_random_password()
        hashed = generate_password_hash(password)

        user = User(
            email=email,
            user_type=user_type,
            password_hash=hashed,
            verification_status=verification_status,
            account_status=account_status,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        db.session.add(user)
        db.session.flush()

        profile = Profile(
            user_id=user.id,
            profile_type=user_type,
            profile_completeness=20,
            visibility_settings='Public',
            last_updated=datetime.utcnow()
        )
        db.session.add(profile)
        db.session.flush()

        # Profile type specific
        if user_type == 'Scientist':
            db.session.add(PIProfile(
                profile_id=profile.id,
                name=full_name,
                affiliation=organization,
                current_designation=designation,
                current_message=bio,
                contact_phone=phone  # ← Save phone
            ))
        elif user_type == 'Student':
            db.session.add(StudentProfile(
                profile_id=profile.id,
                name=full_name,
                affiliation=organization,
                contact_email=email,
                why_me=bio,
                contact_phone=phone
            ))
        elif user_type == 'Industry':
            db.session.add(IndustryProfile(
                profile_id=profile.id,
                company_name=organization,
                contact_person=full_name,
                email=email,
                contact_phone=phone
            ))
        elif user_type == 'Vendor':
            db.session.add(VendorProfile(
                profile_id=profile.id,
                company_name=organization,
                contact_person=full_name,
                email=email,
                contact_phone=phone
            ))

        db.session.add(Register(
            email=email,
            user_type=user_type,
            user_id=user.id,
            profile_id=profile.id,
            verified=True,
            password_hash=password,
            created_at=datetime.utcnow()
        ))

        db.session.commit()

        # Send email with phone
        send_account_details_email(email, {
            'user_type': user_type,
            'full_name': full_name,
            'organization': organization,
            'designation': designation,
            'phone': phone,
            'password': password
        })

        # Clear session
        session.pop('oauth_email', None)
        session.pop('oauth_name', None)
        session.pop('oauth_provider', None)

        if user_type == 'Scientist':
            session['show_pending_modal'] = True
            flash('Account created! Awaiting admin approval.', 'info')
            return redirect(url_for('auth.login'))

        login_user(user)
        flash(f'Welcome {full_name}!', 'success')
        return redirect(_redirect_by_user_type(user))

    # Pre-fill form
    if request.method == 'GET':
        form.email.data = email
        form.full_name.data = name

    return render_template('auth/oauth_register.html',
                           form=form, email=email, name=name, provider=provider.title())