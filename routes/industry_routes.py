# routes\industry_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import Profile, IndustryProfile
from extensions import db  # yeh alag se import karo
from werkzeug.utils import secure_filename
from sqlalchemy import or_
import os

industry_bp = Blueprint('industry', __name__, url_prefix='/industry')

@industry_bp.route('/dashboard')
@login_required
def industry_dashboard():
    if current_user.user_type != 'Industry':
        abort(403)
    profile = Profile.query.filter_by(user_id=current_user.id).first_or_404()
    industry = IndustryProfile.query.filter_by(profile_id=profile.id).first()
    return render_template('industry/dashboard.html', profile=profile, industry=industry)


@industry_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def industryProfile():
    if current_user.user_type != 'Industry':
        abort(403)

    profile = Profile.query.filter_by(user_id=current_user.id).first_or_404()
    industry = IndustryProfile.query.filter_by(profile_id=profile.id).first()

    if request.method == 'POST':
        if not industry:
            industry = IndustryProfile(profile_id=profile.id)

        industry.company_name = request.form['company_name']
        industry.contact_person = request.form['contact_person']
        industry.email = request.form['email']
        industry.contact_phone = request.form['contact_phone']
        industry.gst = request.form['gst']
        industry.pan = request.form['pan']
        industry.address = request.form['address']
        industry.sector = request.form['sector']
        industry.team_size = request.form.get('team_size', type=int)
        industry.annual_turnover = request.form['annual_turnover']
        industry.vision = request.form['vision']

        logo_file = request.files.get('logo')
        if logo_file and logo_file.filename:
            filename = secure_filename(logo_file.filename)
            upload_path = os.path.join('static/uploads/industry_logos', filename)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            logo_file.save(upload_path)
            industry.logo = upload_path

        db.session.add(industry)
        db.session.commit()
        flash("Industry profile saved successfully.", "success")
        return redirect(url_for('industry.industry_profile', industry_id=industry.id))  # <--- pass industry.id here

    return render_template('industry/profile.html', industry=industry)



@industry_bp.route('/<int:industry_id>')
def industry_profile(industry_id):
    industry = IndustryProfile.query.get_or_404(industry_id)
    return render_template('visit_profile/industry.html', industry=industry)

def search_industries(query):
    """Search industries by company name, sector or vision"""
    if not query:
        return IndustryProfile.query.all()
    
    return IndustryProfile.query.filter(
        or_(
            IndustryProfile.company_name.ilike(f'%{query}%'),
            IndustryProfile.sector.ilike(f'%{query}%'),
            IndustryProfile.vision.ilike(f'%{query}%'),
            IndustryProfile.contact_person.ilike(f'%{query}%')
        )
    ).all()

@industry_bp.route('/full-table')
def full_table():
    query = request.args.get('query', '')
    industries = search_industries(query)
    return render_template('industry/full_table.html', 
                         industries=industries,
                         query=query)
