from fastapi import APIRouter

from app.api.routes import files, items, login, pdca, private, users, utils
from app.core.config import settings
from app.web_tests.api import router as web_tests_router

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(files.router)
api_router.include_router(pdca.router)
api_router.include_router(web_tests_router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
