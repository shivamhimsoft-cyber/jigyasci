# routes\technology_routes.py

from flask import Blueprint, render_template, request
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