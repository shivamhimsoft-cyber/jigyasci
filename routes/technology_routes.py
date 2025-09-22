# routes\technology_routes.py

from flask import Blueprint, render_template, request, url_for, redirect
from models import Technology, Profile
from sqlalchemy import or_
from extensions import db

tech_bp = Blueprint('technology', __name__, url_prefix='/technology')

@tech_bp.route('/full-table')
def full_table():
    query = request.args.get('query', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20

    techs_query = Technology.query.join(Profile)

    if query:
        q = f"%{query}%"
        techs_query = techs_query.filter(
            or_(
                Technology.title.ilike(q),
                Technology.keywords.ilike(q),
                Technology.target_industries.ilike(q),
            )
        )

    technologies = techs_query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'faculty/technologies/full_table.html',
        technologies=technologies,
        query=query
    )





@tech_bp.route('/<int:tech_id>')
def view_technology(tech_id):
    technology = Technology.query.get_or_404(tech_id)
    profile = technology.profile  # ✅ Now works

    # Find the profile that owns this technology
    profile = technology.profile

    if not profile:
        return render_template(
            'faculty/technologies/view.html',
            technology=technology
        )

    # PI profile
    if profile.pi_profile:
        return redirect(url_for('faculty_info', profile_id=profile.id))

    # Student profile
    if profile.student_profile:
        return redirect(url_for('student.student_details', student_id=profile.student_profile.id))

    # Vendor profile
    if profile.vendor_profile:
        return redirect(url_for('vendor.vendor_profile', vendor_id=profile.vendor_profile.id))

    # Industry profile
    if profile.industry_profile:
        return redirect(url_for('industry.industry_profile', industry_id=profile.industry_profile.id))

    # fallback → show generic view page
    return render_template('faculty/technologies/full_table.html', technology=technology)

