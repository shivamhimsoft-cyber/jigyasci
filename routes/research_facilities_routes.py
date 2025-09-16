# routes\research_facilities_routes.py

from flask import Blueprint, render_template, request
from models import ResearchFacility, PIProfile
from sqlalchemy import or_
from extensions import db

facility_bp = Blueprint('facility', __name__, url_prefix='/facility')

@facility_bp.route('/full-table')
def full_table():
    query = request.args.get('query', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20

    facilities_query = ResearchFacility.query.join(PIProfile)

    if query:
        q = f"%{query}%"
        facilities_query = facilities_query.filter(
            or_(
                ResearchFacility.equipment_name.ilike(q),
                ResearchFacility.make.ilike(q),
                ResearchFacility.model.ilike(q),
                PIProfile.name.ilike(q),
                PIProfile.affiliation_short.ilike(q)
            )
        )

    facilities = facilities_query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'faculty/research_facilities/full_table.html',
        facilities=facilities,
        query=query
    )


@facility_bp.route('/<int:facility_id>')
def facility_profile(facility_id):
    facility = ResearchFacility.query.get_or_404(facility_id)
    return render_template('faculty/research_facilities/detail.html', facility=facility)
