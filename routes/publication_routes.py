from flask import Blueprint, render_template, request
from models import Publication, Profile, PIProfile, StudentProfile
from sqlalchemy import or_, and_
from extensions import db
from datetime import datetime

pub_bp = Blueprint('publication', __name__, url_prefix='/publication')

@pub_bp.route('/full-table')
def full_table():
    query = request.args.get('query', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Query publications with joined profile information
    pubs_query = db.session.query(
        Publication,
        db.func.coalesce(PIProfile.name, StudentProfile.name).label('author_name'),
        db.func.coalesce(PIProfile.affiliation_short, StudentProfile.affiliation).label('affiliation')
    ).join(
        Profile, Publication.profile_id == Profile.id
    ).outerjoin(
        PIProfile, and_(Profile.id == PIProfile.profile_id, Profile.user.has(user_type='PI'))
    ).outerjoin(
        StudentProfile, and_(Profile.id == StudentProfile.profile_id, Profile.user.has(user_type='Student'))
    )

    if query:
        q = f"%{query}%"
        pubs_query = pubs_query.filter(
            or_(
                Publication.title.ilike(q),
                Publication.authors.ilike(q),
                Publication.journal_or_conference.ilike(q),
                Publication.keywords.ilike(q),
                PIProfile.name.ilike(q),
                StudentProfile.name.ilike(q),
                PIProfile.affiliation_short.ilike(q),
                StudentProfile.affiliation.ilike(q)
            )
        )

    publications = pubs_query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'faculty/publications/full_table.html',
        publications=publications,
        query=query,
        current_year=datetime.now().year  # ✅ This fixes the undefined variable
    )
