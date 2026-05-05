"""API v1 路由配置"""
from fastapi import APIRouter
from .endpoints import router as endpoints_router
from .new_features import router as new_features_router

api_router = APIRouter()

# 注册原有端点
api_router.include_router(endpoints_router)

# 注册新功能端点
api_router.include_router(new_features_router, prefix="/v2", tags=["新功能"])
