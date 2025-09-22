# routes/profile_routes.py

from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from models import Profile, PIProfile, StudentProfile, VendorProfile, IndustryProfile

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

# ---------------- PI PROFILE ----------------
@profile_bp.route('/pi/<int:profile_id>')
def view_pi_profile(profile_id):
    pi = PIProfile.query.filter_by(profile_id=profile_id).first()
    if not pi:
        abort(404, "PI Profile not found")
    profile = pi.profile  # Assuming PIProfile has a relationship to Profile
    if not profile:
        abort(404, "Profile not found")
    return render_template('visit_profile/facultyinfo.html', pi=pi, profile=profile)


# ---------------- STUDENT PROFILE ----------------
@profile_bp.route('/student/<int:profile_id>')
def view_student_profile(profile_id):
    profile = StudentProfile.query.filter_by(profile_id=profile_id).first()
    if not profile:
        abort(404, "Student Profile not found")
    return render_template('visit_profile/student.html', student=profile)

# ---------------- VENDOR PROFILE ----------------
@profile_bp.route('/vendor/<int:profile_id>')
def view_vendor_profile(profile_id):
    profile = VendorProfile.query.filter_by(profile_id=profile_id).first()
    if not profile:
        abort(404, "Vendor Profile not found")
    return render_template('visit_profile/vendor.html', specific_profile=profile)

# ---------------- INDUSTRY PROFILE ----------------
@profile_bp.route('/industry/<int:profile_id>')
def view_industry_profile(profile_id):
    profile = IndustryProfile.query.filter_by(profile_id=profile_id).first()
    if not profile:
        abort(404, "Industry Profile not found")
    return render_template('visit_profile/industry.html', specific_profile=profile)
