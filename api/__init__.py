"""
API routes initialization
"""

from api.clients import router as clients_router
from api.demandes import router as demandes_router
from api.offres import router as offres_router
from api.sites import router as sites_router
from api.activites import router as activites_router
from api.jeux import router as jeux_router
from api.activites_jeux import router as activites_jeux_router
from api.personnel import router as personnel_router
from api.affectations import router as affectations_router
from api.depenses import router as depenses_router
from api.demandes_contact import router as demandes_contact_router
from api.demandes_team_building import router as demandes_team_building_router
from api.demandes_tourisme import router as demandes_tourisme_router
from api.utilisateurs import router as utilisateurs_router
from api.role import router as roles_router
from api.uploads import router as uploads_router
from api.agent.routes import router as agent_router
from api.contact_akan.routes import router as contact_akan_router



def include_api_routes(app):
    """Include all API routes in the application"""
    app.include_router(clients_router)
    app.include_router(demandes_router)
    app.include_router(offres_router)
    app.include_router(sites_router)
    app.include_router(activites_router)
    app.include_router(jeux_router)
    app.include_router(activites_jeux_router)
    app.include_router(personnel_router)
    app.include_router(affectations_router)
    app.include_router(depenses_router)
    app.include_router(demandes_contact_router)
    app.include_router(demandes_team_building_router)
    app.include_router(demandes_tourisme_router)
    app.include_router(utilisateurs_router)
    app.include_router(roles_router)
    app.include_router(uploads_router)
    app.include_router(agent_router)
    app.include_router(contact_akan_router)


