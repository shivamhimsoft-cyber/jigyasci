# routes/student_routes.py

from flask import Blueprint, render_template, abort, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from models import StudentProfile, Profile, Education, Experience, Publication, Skill, Award, TeamMember
from extensions import db
from sqlalchemy import or_

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
@login_required
def student_dashboard():
    if current_user.user_type != 'Student':
        abort(403)
    return render_template('students/dashboard.html', title='Students Dashboard')


@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def student_profile():
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        flash("Profile not found.", "danger")
        return redirect(url_for('student.student_dashboard'))

    student_profile = StudentProfile.query.filter_by(profile_id=profile.id).first()

    if request.method == 'POST':
        if not student_profile:
            student_profile = StudentProfile(profile_id=profile.id)

        student_profile.name = request.form['name']
        student_profile.affiliation = request.form['affiliation']
        student_profile.contact_email = request.form['email']
        student_profile.contact_phone = request.form['contact_phone']
        student_profile.dob = datetime.strptime(request.form['dob'], '%Y-%m-%d') if request.form['dob'] else None
        student_profile.gender = request.form['gender']
        student_profile.address = request.form['address']
        student_profile.research_interests = request.form['current_focus']
        
        student_profile.why_me = request.form['why_join_lab']
        student_profile.current_status = request.form['current_message']

        db.session.add(student_profile)
        db.session.commit()
        flash("Student profile updated successfully.", "success")
        return redirect(url_for('student.student_profile'))

    return render_template('students/student_profile.html', profile=student_profile)


@student_bp.route('/dashboard')
@login_required
def studentProfile():
    if current_user.user_type != 'Student':
        abort(403)
    return render_template('students/dashboard.html', title='Students Dashboard')



@student_bp.route('/<int:student_id>')
def student_details(student_id):
    student = StudentProfile.query.get_or_404(student_id)
    profile = student.profile

    educations = Education.query.filter_by(profile_id=profile.id).order_by(Education.start_year.desc()).all()
    experiences = Experience.query.filter_by(profile_id=profile.id).order_by(Experience.start_date.desc()).all()
    publications = Publication.query.filter_by(profile_id=profile.id).order_by(Publication.year.desc()).all()
    skills = Skill.query.filter_by(profile_id=profile.id).order_by(Skill.proficiency_level.desc()).all()
    awards = Award.query.filter_by(profile_id=profile.id).order_by(Award.date.desc()).all()

    team_memberships = TeamMember.query.filter_by(student_profile_id=student_id).all()

    return render_template(
        'visit_profile/student.html',
        student=student,
        profile=profile,
        educations=educations,
        experiences=experiences,
        publications=publications,
        skills=skills,
        awards=awards,
        team_memberships=team_memberships
    )

def search_students(query):
    """Search students by name, affiliation, or research interests"""
    if not query:
        return StudentProfile.query.all()  # Return all students if no query
    
    # Perform a case-insensitive search across multiple fields
    return StudentProfile.query.filter(
        or_(
            StudentProfile.name.ilike(f'%{query}%'),
            StudentProfile.affiliation.ilike(f'%{query}%'),
            StudentProfile.research_interests.ilike(f'%{query}%'),
        )
    ).all()

@student_bp.route('/full-table', methods=['GET'])
def full_table():
    query = request.args.get('query', '')
    students = search_students(query)
    return render_template('students/full_table.html', 
                         students=students, 
                         query=query)














