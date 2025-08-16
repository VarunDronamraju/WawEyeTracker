from fastapi import APIRouter

from .auth import router as auth_router
from .blink import router as blink_router
from .gdpr import router as gdpr_router

api_router = APIRouter()

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(blink_router)
api_router.include_router(gdpr_router)