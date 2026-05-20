"""API v1 root router — aggregates all entity routers."""

from fastapi import APIRouter

from app.api.v1.routers.authors import router as authors_router
from app.api.v1.routers.books import router as books_router
from app.api.v1.routers.categories import router as categories_router
from app.api.v1.routers.loans import router as loans_router
from app.api.v1.routers.returns import router as returns_router
from app.api.v1.routers.roles import router as roles_router
from app.api.v1.routers.users import router as users_router

api_router = APIRouter()

api_router.include_router(roles_router)
api_router.include_router(users_router)
api_router.include_router(categories_router)
api_router.include_router(authors_router)
api_router.include_router(books_router)
api_router.include_router(loans_router)
api_router.include_router(returns_router)

__all__ = ["api_router"]
