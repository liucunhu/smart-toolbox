"""
Webpack HMR 路由 - 处理前端开发服务器的热更新请求
"""
from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter()

@router.get("/__webpack_hmr")
async def webpack_hmr():
    """
    处理前端开发服务器的 HMR 请求，避免 404 日志
    这个路由专门处理前端开发时的热更新请求
    """
    return Response(content="OK", media_type="text/plain")

@router.head("/__webpack_hmr")
async def webpack_hmr_head():
    """
    处理前端开发服务器的 HEAD 请求
    """
    return Response(status_code=200)