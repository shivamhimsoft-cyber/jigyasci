# routes/pi_routes.py

from flask import Blueprint, render_template, abort, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import PIProfile, Profile, TeamMember, Education, Experience, ResearchFacility, Publication, Technology, Skill, SkillType, Award, Project, StudentProfile, EquipmentType
from extensions import db
from sqlalchemy import func, or_
from datetime import datetime
from werkzeug.utils import secure_filename
import os

pi_bp = Blueprint('pi', __name__, url_prefix='/faculty')

# DASHBOARD

@pi_bp.route('/dashboard')
@login_required
def faculty_dashboard():
    if current_user.user_type != 'PI':
        abort(403)
    return render_template('faculty/dashboard.html', title='Faculty Dashboard')


# BASIC INFORMATION

@pi_bp.route('/basic_info', methods=['GET', 'POST'])
@login_required
def basic_info():
    if current_user.user_type != 'PI':
        abort(403)

    profile = current_user.profile.pi_profile

    if request.method == 'POST':
        if not profile:
            profile = PIProfile(profile_id=current_user.profile.id)
            db.session.add(profile)

        profile.name = request.form.get('name')
        profile.department = request.form.get('department')
        profile.affiliation = request.form.get('affiliation')
        profile.gender = request.form.get('gender')
        profile.email = request.form.get('email')
        profile.contact_phone = request.form.get('contact_phone')
        profile.address = request.form.get('address')
        profile.current_message = request.form.get('current_message')
        profile.current_focus = request.form.get('current_focus')
        profile.expectations_from_students = request.form.get('expectations')
        profile.why_join_lab = request.form.get('why_join_lab')

        dob_str = request.form.get('dob')
        start_date_str = request.form.get('start_date')
        profile.dob = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None
        profile.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('pi.view_pi_profile'))

    return render_template('faculty/basic_info.html', profile=profile)



# PROFILE

@pi_bp.route('/pi_profile')
@login_required
def view_pi_profile():
    if current_user.user_type != 'PI':
        abort(403)
    
    profile = current_user.profile.pi_profile
    if not profile:
        flash('Profile not found', 'error')
        return redirect(url_for('pi.basic_info'))
    
    return render_template('faculty/profile.html', profile=profile)


# EDUCATION
@pi_bp.route('/education', methods=['GET', 'POST'])
@login_required
def education():
    if request.method == 'POST':
        education_id = request.form.get('education_id')
        degree_name = request.form.get('degree_name')
        college = request.form.get('college')
        university = request.form.get('university')
        university_address = request.form.get('university_address')
        start_year = request.form.get('start_year')
        end_year = request.form.get('end_year')
        currently_pursuing = request.form.get('currently_pursuing') == 'on'

        # Server-side validation
        if end_year and not currently_pursuing:
            try:
                if int(end_year) < int(start_year):
                    flash("❌ End Year must be greater than or equal to Start Year.", "error")
                    return redirect(url_for('pi.education'))
            except ValueError:
                flash("❌ Invalid year format provided.", "error")
                return redirect(url_for('pi.education'))

        if education_id:
            edu = Education.query.get_or_404(int(education_id))
            if edu.profile_id != current_user.profile.id:
                abort(403)
            edu.degree_name = degree_name
            edu.college = college
            edu.university = university
            edu.university_address = university_address
            edu.start_year = start_year
            edu.end_year = end_year
            edu.currently_pursuing = currently_pursuing
            flash("✅ Education updated successfully!", "success")
        else:
            new_edu = Education(
                degree_name=degree_name,
                college=college,
                university=university,
                university_address=university_address,
                start_year=start_year,
                end_year=end_year,
                currently_pursuing=currently_pursuing,
                profile_id=current_user.profile.id
            )
            db.session.add(new_edu)
            flash("✅ Education added successfully!", "success")

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("An error occurred while saving education data.", "error")
        return redirect(url_for('pi.education'))

    # Get pagination parameters from request
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Get both paginated and all records (for any existing functionality)
    educations_paginated = Education.query.filter_by(profile_id=current_user.profile.id)\
                               .order_by(Education.start_year.desc())\
                               .paginate(page=page, per_page=per_page, error_out=False)
    
    educations_all = Education.query.filter_by(profile_id=current_user.profile.id).all()
    
    return render_template('faculty/education.html', 
                         educations=educations_paginated,
                         all_educations=educations_all)

@pi_bp.route('/education/<int:id>/delete', methods=['POST'])
@login_required
def delete_education(id):
    education = Education.query.get_or_404(id)
    if education.profile_id != current_user.profile.id:
        abort(403)
    db.session.delete(education)
    db.session.commit()
    flash('Education deleted successfully.', 'success')
    return redirect(url_for('pi.education'))

    


# EXPERIENCE

@pi_bp.route('/experience', methods=['GET', 'POST'])
@login_required
def experience():
    if request.method == 'POST':
        experience_id = request.form.get('experience_id')
        project_title = request.form.get('project_title')
        position = request.form.get('position')
        pi = request.form.get('pi')
        pi_affiliation = request.form.get('pi_affiliation')
        college = request.form.get('college')
        university_or_industry = request.form.get('university_or_industry')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        currently_working = True if request.form.get('currently_working') == 'on' else False

        # ✅ Server-side validation: End Date >= Start Date
        if start_date and end_date:
            try:
                sd = datetime.strptime(start_date, "%Y-%m-%d")
                ed = datetime.strptime(end_date, "%Y-%m-%d")
                if ed < sd:
                    flash("End Date must be greater than or equal to Start Date.", "error")
                    return redirect(url_for('pi.experience'))
            except ValueError:
                flash("Invalid date format.", "error")
                return redirect(url_for('pi.experience'))

        if experience_id:
            exp = Experience.query.get_or_404(int(experience_id))
            if exp.profile_id != current_user.profile.id:
                abort(403)
            exp.project_title = project_title
            exp.position = position
            exp.pi = pi
            exp.pi_affiliation = pi_affiliation
            exp.college = college
            exp.university_or_industry = university_or_industry
            exp.start_date = start_date
            exp.end_date = end_date
            exp.currently_working = currently_working
            flash("Experience updated successfully!", "success")
        else:
            new_exp = Experience(
                project_title=project_title,
                position=position,
                pi=pi,
                pi_affiliation=pi_affiliation,
                college=college,
                university_or_industry=university_or_industry,
                start_date=start_date,
                end_date=end_date,
                currently_working=currently_working,
                profile_id=current_user.profile.id
            )
            db.session.add(new_exp)
            flash("Experience added successfully!", "success")

        db.session.commit()
        return redirect(url_for('pi.experience'))

     # Get page number from request (default to 1)
    page = request.args.get('page', 1, type=int)
    # Get items per page from request (default to 10)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Create pagination object while keeping original query
    experiences_paginated = Experience.query.filter_by(profile_id=current_user.profile.id)\
                                 .paginate(page=page, per_page=per_page, error_out=False)
    
    # Keep original non-paginated query for any existing template usage
    experiences_all = Experience.query.filter_by(profile_id=current_user.profile.id).all()
    
    return render_template('faculty/experience.html', 
                         experiences=experiences_paginated.items,
                         all_experiences=experiences_all,
                         pagination=experiences_paginated)

    # experiences = Experience.query.filter_by(profile_id=current_user.profile.id).all()
    # return render_template('faculty/experience.html', experiences=experiences)



@pi_bp.route('/experience/delete/<int:id>', methods=['POST'])
@login_required
def delete_experience(id):
    exp = Experience.query.get_or_404(id)
    if exp.profile_id != current_user.profile.id:
        abort(403)
    db.session.delete(exp)
    db.session.commit()
    flash("Experience deleted successfully!", "success")
    return redirect(url_for('pi.experience'))




# PUBLICATIONS

@pi_bp.route('/publications', methods=['GET', 'POST'])
@login_required
def publications():
    current_year = datetime.now().year
    
    if request.method == 'POST':
        publication_id = request.form.get('publication_id')
        title = request.form.get('title')
        authors = request.form.get('authors')
        journal_or_conference = request.form.get('journal_or_conference')
        year = request.form.get('year')
        doi = request.form.get('doi')
        citation = request.form.get('citation')
        abstract = request.form.get('abstract')
        keywords = request.form.get('keywords')

        # Validate year
        try:
            year = int(year)
            if year < 1900 or year > current_year + 2:
                flash(f"Year must be between 1900 and {current_year + 2}", "error")
                return redirect(url_for('pi.publications'))
        except ValueError:
            flash("Invalid year format", "error")
            return redirect(url_for('pi.publications'))

        if publication_id:
            pub = Publication.query.get_or_404(int(publication_id))
            if pub.profile_id != current_user.profile.id:
                abort(403)
            pub.title = title
            pub.authors = authors
            pub.journal_or_conference = journal_or_conference
            pub.year = year
            pub.doi = doi
            pub.citation = citation
            pub.abstract = abstract
            pub.keywords = keywords
            flash("Publication updated successfully!", "success")
        else:
            new_pub = Publication(
                title=title,
                authors=authors,
                journal_or_conference=journal_or_conference,
                year=year,
                doi=doi,
                citation=citation,
                abstract=abstract,
                keywords=keywords,
                profile_id=current_user.profile.id
            )
            db.session.add(new_pub)
            flash("Publication added successfully!", "success")

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("An error occurred while saving the publication.", "error")
        return redirect(url_for('pi.publications'))

    # Handle GET request with pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    publications = Publication.query.filter_by(profile_id=current_user.profile.id)\
                        .order_by(Publication.year.desc())\
                        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('faculty/publications.html', 
                         publications=publications,
                         current_year=current_year)

@pi_bp.route('/publications/delete/<int:id>', methods=['POST'])
@login_required
def delete_publication(id):
    pub = Publication.query.get_or_404(id)
    if pub.profile_id != current_user.profile.id:
        abort(403)
    db.session.delete(pub)
    db.session.commit()
    flash("Publication deleted successfully!", "success")
    return redirect(url_for('pi.publications'))




# PROJECTS

@pi_bp.route('/projects', methods=['GET', 'POST'])
@login_required
def projects():
    if not current_user.profile or not current_user.profile.pi_profile:
        abort(403)
        
    if request.method == 'POST':
        project_id = request.form.get('project_id')
        title = request.form.get('title')
        funding_agency = request.form.get('funding_agency')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        status = request.form.get('status')
        description = request.form.get('description')
        keywords = request.form.get('keywords')

        # Validation
        if start_date and end_date:
            try:
                sd = datetime.strptime(start_date, "%Y-%m-%d")
                ed = datetime.strptime(end_date, "%Y-%m-%d")
                if ed < sd:
                    flash("End Date must be after Start Date", "error")
                    return redirect(url_for('pi.projects'))
            except ValueError:
                flash("Invalid date format", "error")
                return redirect(url_for('pi.projects'))

        if project_id:
            project = Project.query.get_or_404(int(project_id))
            if project.pi_profile_id != current_user.profile.pi_profile.id:
                abort(403)
            project.title = title
            project.funding_agency = funding_agency
            project.start_date = start_date
            project.end_date = end_date
            project.status = status
            project.description = description
            project.keywords = keywords
            flash("Project updated successfully!", "success")
        else:
            new_project = Project(
                title=title,
                funding_agency=funding_agency,
                start_date=start_date,
                end_date=end_date,
                status=status,
                description=description,
                keywords=keywords,
                pi_profile_id=current_user.profile.pi_profile.id
            )
            db.session.add(new_project)
            flash("Project added successfully!", "success")

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("An error occurred while saving the project", "error")
        
        return redirect(url_for('pi.projects'))

    # Get paginated projects
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    projects = Project.query.filter_by(pi_profile_id=current_user.profile.pi_profile.id)\
                  .order_by(Project.start_date.desc())\
                  .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('faculty/projects.html', projects=projects)

@pi_bp.route('/projects/delete/<int:id>', methods=['POST'])
@login_required
def delete_project(id):
    project = Project.query.get_or_404(id)
    if not current_user.profile or not current_user.profile.pi_profile or project.pi_profile_id != current_user.profile.pi_profile.id:
        abort(403)
    db.session.delete(project)
    db.session.commit()
    flash("Project deleted successfully!", "success")
    return redirect(url_for('pi.projects'))




# TECHNOLOGIES 

@pi_bp.route('/technologies', methods=['GET', 'POST'])
@login_required
def technologies():
    if not current_user.profile:
        abort(403)
        
    if request.method == 'POST':
        technology_id = request.form.get('technology_id')
        title = request.form.get('title')
        description = request.form.get('description')
        keywords = request.form.get('keywords')
        trl = request.form.get('trl')
        usp = request.form.get('usp')
        target_industries = request.form.get('target_industries')
        ip_status = request.form.get('ip_status')
        licensing_intent = request.form.get('licensing_intent')

        # Basic validation
        if not title:
            flash("Title is required", "error")
            return redirect(url_for('pi.technologies'))

        if technology_id:
            tech = Technology.query.get_or_404(int(technology_id))
            if tech.creator_profile_id != current_user.profile.id:
                abort(403)
            tech.title = title
            tech.description = description
            tech.keywords = keywords
            tech.trl = trl
            tech.usp = usp
            tech.target_industries = target_industries
            tech.ip_status = ip_status
            tech.licensing_intent = licensing_intent
            flash("Technology updated successfully!", "success")
        else:
            new_tech = Technology(
                title=title,
                description=description,
                keywords=keywords,
                trl=trl,
                usp=usp,
                target_industries=target_industries,
                ip_status=ip_status,
                licensing_intent=licensing_intent,
                creator_profile_id=current_user.profile.id
            )
            db.session.add(new_tech)
            flash("Technology added successfully!", "success")

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("An error occurred while saving the technology", "error")
        
        return redirect(url_for('pi.technologies'))

    # Get paginated technologies
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    technologies = Technology.query.filter_by(creator_profile_id=current_user.profile.id)\
                         .order_by(Technology.updated_at.desc())\
                         .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('faculty/technologies.html', technologies=technologies)

@pi_bp.route('/technologies/delete/<int:id>', methods=['POST'])
@login_required
def delete_technology(id):
    tech = Technology.query.get_or_404(id)
    if not current_user.profile or tech.creator_profile_id != current_user.profile.id:
        abort(403)
    db.session.delete(tech)
    db.session.commit()
    flash("Technology deleted successfully!", "success")
    return redirect(url_for('pi.technologies'))



# RESEACH FACILITIES

UPLOAD_SUBDIR = os.path.join('uploads', 'sops')  # Relative for DB
UPLOAD_FOLDER = os.path.join('static', UPLOAD_SUBDIR)  # Full path
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@pi_bp.route('/research-facilities', methods=['GET', 'POST'])
@login_required
def research_facilities():
    if not current_user.profile or not current_user.profile.pi_profile:
        abort(403)

    if request.method == 'POST':
        facility_id = request.form.get('facility_id')
        equipment_name = request.form.get('equipment_name')
        make = request.form.get('make')
        model = request.form.get('model')
        working_status = request.form.get('working_status')
        equipment_type = request.form.get('equipment_type')

        sop_file = None
        if 'sop_file' in request.files:
            file = request.files['sop_file']
            if file.filename != '':
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    try:
                        file.save(filepath)
                        sop_file = os.path.join('uploads', 'sops', filename)
                    except Exception as e:
                        flash(f"File save error: {str(e)}", "error")
                else:
                    flash("Invalid file type.", "error")

        if not equipment_name:
            flash("Equipment name is required", "error")
            return redirect(url_for('pi.research_facilities'))

        if facility_id:
            facility = ResearchFacility.query.get_or_404(int(facility_id))
            if facility.pi_profile_id != current_user.profile.pi_profile.id:
                abort(403)
            facility.equipment_name = equipment_name
            facility.make = make
            facility.model = model
            facility.working_status = working_status
            facility.equipment_type = equipment_type
            if sop_file:
                if facility.sop_file:
                    old_path = os.path.join('static', facility.sop_file)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                facility.sop_file = sop_file
            flash("Research facility updated successfully!", "success")
        else:
            new_facility = ResearchFacility(
                equipment_name=equipment_name,
                make=make,
                model=model,
                working_status=working_status,
                equipment_type=equipment_type,
                sop_file=sop_file,
                pi_profile_id=current_user.profile.pi_profile.id
            )
            db.session.add(new_facility)
            flash("Research facility added successfully!", "success")

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash("An error occurred while saving the facility", "error")

        return redirect(url_for('pi.research_facilities'))

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    facilities = ResearchFacility.query.filter_by(pi_profile_id=current_user.profile.pi_profile.id)\
        .order_by(ResearchFacility.equipment_name.asc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    # Get equipment types from database
    equipment_types = EquipmentType.query.filter_by(status='Active').all()

    return render_template('faculty/research_facilities.html', 
                         facilities=facilities, 
                         equipment_types=equipment_types)



@pi_bp.route('/research-facilities/delete/<int:id>', methods=['POST'])
@login_required
def delete_research_facility(id):
    facility = ResearchFacility.query.get_or_404(id)
    if not current_user.profile or not current_user.profile.pi_profile or facility.pi_profile_id != current_user.profile.pi_profile.id:
        abort(403)

    if facility.sop_file:
        full_path = os.path.join('static', facility.sop_file)
        if os.path.exists(full_path):
            os.remove(full_path)

    db.session.delete(facility)
    db.session.commit()
    flash("Research facility deleted successfully!", "success")
    return redirect(url_for('pi.research_facilities'))

@pi_bp.route('/download-sop/<int:facility_id>')
@login_required
def download_sop(facility_id):
    facility = ResearchFacility.query.get_or_404(facility_id)
    if not facility.sop_file:
        abort(404)
    
    file_path = os.path.join('static', facility.sop_file)
    if not os.path.exists(file_path):
        abort(404)
    
    return send_file(file_path, as_attachment=True)





# SKILLS

# SKILLS
@pi_bp.route('/skills', methods=['GET', 'POST'])
@login_required
def skills():
    if not current_user.profile:
        abort(403)
        
    if request.method == 'POST':
        skill_id = request.form.get('skill_id')
        skill_type = request.form.get('skill_type')
        skill_name = request.form.get('skill_name')
        proficiency_level = request.form.get('proficiency_level')

        # Validation
        if not all([skill_type, skill_name]):
            flash("Skill type and name are required", "error")
            return redirect(url_for('pi.skills'))

        if skill_id:
            skill = Skill.query.get_or_404(int(skill_id))
            if skill.profile_id != current_user.profile.id:
                abort(403)
            skill.skill_type = skill_type
            skill.skill_name = skill_name
            skill.proficiency_level = proficiency_level
            flash("Skill updated successfully!", "success")
        else:
            new_skill = Skill(
                skill_type=skill_type,
                skill_name=skill_name,
                proficiency_level=proficiency_level,
                profile_id=current_user.profile.id
            )
            db.session.add(new_skill)
            flash("Skill added successfully!", "success")

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("An error occurred while saving the skill", "error")
        
        return redirect(url_for('pi.skills'))

    # Get paginated skills
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    skills = Skill.query.filter_by(profile_id=current_user.profile.id)\
              .order_by(Skill.skill_type.asc(), Skill.skill_name.asc())\
              .paginate(page=page, per_page=per_page, error_out=False)
    
    # Get skill types from database
    skill_types = SkillType.query.filter_by(status='Active').all()
    
    return render_template('faculty/skills.html', skills=skills, skill_types=skill_types)

@pi_bp.route('/skills/delete/<int:id>', methods=['POST'])
@login_required
def delete_skill(id):
    skill = Skill.query.get_or_404(id)
    if not current_user.profile or skill.profile_id != current_user.profile.id:
        abort(403)
    db.session.delete(skill)
    db.session.commit()
    flash("Skill deleted successfully!", "success")
    return redirect(url_for('pi.skills'))



# AWARDS

@pi_bp.route('/awards', methods=['GET', 'POST'])
@login_required
def awards():
    if not current_user.profile:
        abort(403)
        
    if request.method == 'POST':
        award_id = request.form.get('award_id')
        title = request.form.get('title')
        date = request.form.get('date')
        description = request.form.get('description')
        issuing_organization = request.form.get('issuing_organization')

        # Validation
        if not all([title, date]):
            flash("Title and date are required", "error")
            return redirect(url_for('pi.awards'))

        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
            if date_obj > datetime.now().date():
                flash("Award date cannot be in the future", "error")
                return redirect(url_for('awards'))
        except ValueError:
            flash("Invalid date format", "error")
            return redirect(url_for('pi.awards'))

        if award_id:
            award = Award.query.get_or_404(int(award_id))
            if award.profile_id != current_user.profile.id:
                abort(403)
            award.title = title
            award.date = date_obj
            award.description = description
            award.issuing_organization = issuing_organization
            flash("Award updated successfully!", "success")
        else:
            new_award = Award(
                title=title,
                date=date_obj,
                description=description,
                issuing_organization=issuing_organization,
                profile_id=current_user.profile.id
            )
            db.session.add(new_award)
            flash("Award added successfully!", "success")

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("An error occurred while saving the award", "error")
        
        return redirect(url_for('pi.awards'))

    # Get paginated awards
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    awards = Award.query.filter_by(profile_id=current_user.profile.id)\
              .order_by(Award.date.desc())\
              .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('faculty/awards.html', awards=awards)


@pi_bp.route('/awards/delete/<int:id>', methods=['POST'])
@login_required
def delete_award(id):
    award = Award.query.get_or_404(id)
    if not current_user.profile or award.profile_id != current_user.profile.id:
        abort(403)
    db.session.delete(award)
    db.session.commit()
    flash("Award deleted successfully!", "success")
    return redirect(url_for('pi.awards'))




# TEAM MEMBERS

@pi_bp.route('/team-members', methods=['GET', 'POST'])
@login_required
def team_members():
    if not current_user.profile or not current_user.profile.pi_profile:
        abort(403)
        
    if request.method == 'POST':
        member_id = request.form.get('member_id')
        student_profile_id = request.form.get('student_profile_id')
        name = request.form.get('name')
        position = request.form.get('position')
        status = request.form.get('status')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        # Validation
        if not student_profile_id and not name:
            flash("Either select a student or provide a name for external members", "error")
            return redirect(url_for('pi.team_members'))

        if status == 'Former' and not end_date:
            flash("End date is required for former members", "error")
            return redirect(url_for('pi.team_members'))

        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
            
            if end_date_obj and start_date_obj and end_date_obj < start_date_obj:
                flash("End date must be after start date", "error")
                return redirect(url_for('pi.team_members'))
        except ValueError:
            flash("Invalid date format", "error")
            return redirect(url_for('pi.team_members'))

        if member_id:
            member = TeamMember.query.get_or_404(int(member_id))
            if member.pi_profile_id != current_user.profile.pi_profile.id:
                abort(403)
            member.student_profile_id = student_profile_id if student_profile_id else None
            member.name = name if not student_profile_id else None
            member.position = position
            member.status = status
            member.start_date = start_date_obj
            member.end_date = end_date_obj
            flash("Team member updated successfully!", "success")
        else:
            new_member = TeamMember(
                pi_profile_id=current_user.profile.pi_profile.id,
                student_profile_id=student_profile_id if student_profile_id else None,
                name=name if not student_profile_id else None,
                position=position,
                status=status,
                start_date=start_date_obj,
                end_date=end_date_obj
            )
            db.session.add(new_member)
            flash("Team member added successfully!", "success")

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("An error occurred while saving team member", "error")
        
        return redirect(url_for('pi.team_members'))

    # Get paginated team members
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    team_members = TeamMember.query.filter_by(pi_profile_id=current_user.profile.pi_profile.id)\
                          .order_by(TeamMember.status.asc(), TeamMember.start_date.desc())\
                          .paginate(page=page, per_page=per_page, error_out=False)
    
    # Get list of students for dropdown
    students = StudentProfile.query.all()
    
    return render_template('faculty/team_members.html', 
                         team_members=team_members,
                         students=students)

@pi_bp.route('/team-members/delete/<int:id>', methods=['POST'])
@login_required
def delete_team_member(id):
    member = TeamMember.query.get_or_404(id)
    if not current_user.profile or not current_user.profile.pi_profile or member.pi_profile_id != current_user.profile.pi_profile.id:
        abort(403)
    db.session.delete(member)
    db.session.commit()
    flash("Team member deleted successfully!", "success")
    return redirect(url_for('pi.team_members'))




# VIEW FULL TABLE 

@pi_bp.route('/full-table')
def faculty_full_table():
    query = request.args.get('query', '').strip()
    department_filter = request.args.get('department', '').strip()
    location_filter = request.args.get('location', '').strip()
    min_papers = request.args.get('min_papers', '').strip()
    min_experience = request.args.get('min_experience', '').strip()
    max_experience = request.args.get('max_experience', '').strip()
    min_hindex = request.args.get('min_hindex', '').strip()

    page = int(request.args.get('page', 1))
    sort = request.args.get('sort', 'name')
    direction = request.args.get('direction', 'asc')
    per_page = 20

    sort_field_map = {
        'name': PIProfile.name,
        'research_focus': PIProfile.current_focus,
        'designation': PIProfile.current_designation,
        'affiliation': PIProfile.affiliation_short,
        'department': PIProfile.department,
        'location': PIProfile.location,
        'papers': PIProfile.papers_published,
        'citations': PIProfile.total_citations,
        'experience': PIProfile.research_experience_years,
        'h_index': PIProfile.h_index,
    }

    profiles_query = Profile.query.join(PIProfile)

    if query:
        q = f"%{query}%"
        profiles_query = profiles_query.filter(
            or_(
                func.lower(func.replace(PIProfile.name, ' ', '')).ilike(f"%{query.replace(' ', '').lower()}%"),
                PIProfile.department.ilike(q),
                PIProfile.affiliation.ilike(q),
                PIProfile.affiliation_short.ilike(q),
                PIProfile.location.ilike(q),
                PIProfile.current_designation.ilike(q),
                PIProfile.current_focus.ilike(q)
            )
        )

    if department_filter:
        profiles_query = profiles_query.filter(PIProfile.department == department_filter)

    if location_filter:
        profiles_query = profiles_query.filter(PIProfile.location == location_filter)

    if min_papers.startswith('>'):
        try:
            value = int(min_papers[1:])
            profiles_query = profiles_query.filter(PIProfile.papers_published > value)
        except ValueError:
            pass
    elif min_papers.isdigit():
        profiles_query = profiles_query.filter(PIProfile.papers_published <= int(min_papers))

    if min_experience.startswith('>'):
        try:
            value = int(min_experience[1:])
            profiles_query = profiles_query.filter(PIProfile.research_experience_years > value)
        except ValueError:
            pass
    elif min_experience.isdigit():
        profiles_query = profiles_query.filter(PIProfile.research_experience_years <= int(min_experience))

    if min_hindex.startswith('>'):
        try:
            value = int(min_hindex[1:])
            profiles_query = profiles_query.filter(PIProfile.h_index > value)
        except ValueError:
            pass
    elif min_hindex.isdigit():
        profiles_query = profiles_query.filter(PIProfile.h_index <= int(min_hindex))

    sort_field = sort_field_map.get(sort, PIProfile.name)
    if direction == 'asc':
        profiles_query = profiles_query.order_by(sort_field.asc().nulls_last())
    else:
        profiles_query = profiles_query.order_by(sort_field.desc().nulls_last())

    profiles_paginated = profiles_query.paginate(page=page, per_page=per_page, error_out=False)

    departments = [d[0] for d in db.session.query(PIProfile.department).distinct().order_by(PIProfile.department).all() if d[0]]
    locations = [l[0] for l in db.session.query(PIProfile.location).distinct().order_by(PIProfile.location).all() if l[0]]

    return render_template(
        'faculty/full_table.html',
        query=query,
        profiles=profiles_paginated,
        page=page,
        total_pages=profiles_paginated.pages,
        sort=sort,
        direction=direction,
        departments=departments,
        locations=locations,
        selected_department=department_filter,
        selected_location=location_filter,
        min_papers=min_papers,
        min_experience=min_experience,
        min_hindex=min_hindex
    )






