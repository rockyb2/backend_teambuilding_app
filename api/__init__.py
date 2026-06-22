"""
API routes initialization
"""

from api.clients import router as clients_router
from api.demandes import router as demandes_router
from api.offres import router as offres_router
from api.offres_tourisme import router as offres_tourisme_router
from api.proformas import router as proformas_router
from api.proformas_tourisme import router as proformas_tourisme_router
from api.sites import router as sites_router
from api.activites import router as activites_router
from api.jeux import router as jeux_router
from api.activites_jeux import router as activites_jeux_router
from api.activites_benevoles import router as activites_benevoles_router
from api.activites_materiels import router as activites_materiels_router
from api.personnel import router as personnel_router
from api.affectations import router as affectations_router
from api.materiels import router as materiels_router
from api.materiels_production import router as materiels_production_router
from api.depenses import router as depenses_router
from api.categories_depenses import router as categories_depenses_router
from api.benevoles import router as benevoles_router
from api.dashboard_teambuilding import router as dashboard_teambuilding_router
from api.demandes_contact import router as demandes_contact_router
from api.demandes_team_building import router as demandes_team_building_router
from api.demandes_tourisme import router as demandes_tourisme_router
from api.newsletter import router as newsletter_router
from api.circuits_touristiques import router as circuits_touristiques_router
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
    app.include_router(offres_tourisme_router)
    app.include_router(proformas_router)
    app.include_router(proformas_tourisme_router)
    app.include_router(sites_router)
    app.include_router(activites_router)
    app.include_router(jeux_router)
    app.include_router(activites_jeux_router)
    app.include_router(activites_benevoles_router)
    app.include_router(activites_materiels_router)
    app.include_router(personnel_router)
    app.include_router(affectations_router)
    app.include_router(materiels_router)
    app.include_router(materiels_production_router)
    app.include_router(depenses_router)
    app.include_router(categories_depenses_router)
    app.include_router(benevoles_router)
    app.include_router(dashboard_teambuilding_router)
    app.include_router(demandes_contact_router)
    app.include_router(demandes_team_building_router)
    app.include_router(demandes_tourisme_router)
    app.include_router(newsletter_router)
    app.include_router(circuits_touristiques_router)
    app.include_router(utilisateurs_router)
    app.include_router(roles_router)
    app.include_router(uploads_router)
    app.include_router(agent_router)
    app.include_router(contact_akan_router)


