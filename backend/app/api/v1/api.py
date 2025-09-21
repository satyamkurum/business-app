# backend/app/api/v1/api.py

from fastapi import APIRouter
from .endpoints import menu, promotions, restaurant, chat, sync, owner, payments

api_router = APIRouter()
api_router.include_router(menu.router, prefix="/menu")
api_router.include_router(promotions.router, prefix="/promotions")
api_router.include_router(restaurant.router, prefix="/restaurant")
api_router.include_router(chat.router, prefix="/chats")
api_router.include_router(sync.router, prefix="/sync")
api_router.include_router(owner.router, prefix="/owner")
api_router.include_router(payments.router, prefix="/payments") 