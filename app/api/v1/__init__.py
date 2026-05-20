"""API v1 路由配置"""
from fastapi import APIRouter
from .endpoints import router as endpoints_router
from .new_features import router as new_features_router
from .webpack_hmr_router import router as webpack_hmr_router
from .agent_collaboration import router as agent_collaboration_router
from .autonomous_agents import router as autonomous_agents_router

api_router = APIRouter()

# 注册原有端点
api_router.include_router(endpoints_router)

# 注册 HMR 路由
api_router.include_router(webpack_hmr_router)

# 注册新功能端点
api_router.include_router(new_features_router, prefix="/v2", tags=["新功能"])

# 注册智能体协作端点
api_router.include_router(agent_collaboration_router)

# 注册自主智能体端点
api_router.include_router(autonomous_agents_router)
