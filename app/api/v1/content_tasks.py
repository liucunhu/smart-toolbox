"""
内容任务管理API端点
扩展内容任务的完整功能：重试、取消、统计等
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import ContentTask
from typing import Optional
from app.utils.logger import logger

router = APIRouter()


@router.get("/content/tasks", summary="获取内容创作任务列表")
def list_content_tasks(
    platform: Optional[str] = Query(None, description="平台筛选"),
    task_type: Optional[str] = Query(None, description="任务类型筛选：generate_script/process_video/generate_cover/compliance_check/publish"),
    status: Optional[str] = Query(None, description="状态筛选：pending/processing/completed/failed/cancelled"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取内容创作任务列表（包含发布记录、支持分页和筛选）"""
    query = db.query(ContentTask)
    
    # 筛选条件
    if platform:
        query = query.filter(ContentTask.target_platform == platform)
    if task_type:
        query = query.filter(ContentTask.task_type == task_type)
    if status:
        query = query.filter(ContentTask.status == status)
    
    # 计算总数
    total = query.count()
    
    # 分页查询
    skip = (page - 1) * page_size
    tasks = query.order_by(ContentTask.created_at.desc()).offset(skip).limit(page_size).all()
    
    # 统计数据
    all_tasks = db.query(ContentTask).all()
    statistics = {
        "total": len(all_tasks),
        "processing": len([t for t in all_tasks if t.status == "processing"]),
        "completed": len([t for t in all_tasks if t.status == "completed"]),
        "failed": len([t for t in all_tasks if t.status == "failed"])
    }
    
    return {
        "status": "success",
        "data": {
            "items": [
                {
                    "id": t.id,
                    "task_id": t.task_id if hasattr(t, 'task_id') else str(t.id),
                    "task_type": t.task_type if hasattr(t, 'task_type') else "unknown",
                    "target_platform": t.target_platform.value if hasattr(t.target_platform, 'value') else str(t.target_platform),
                    "original_topic": t.original_topic,
                    "article_title": t.article_title,
                    "article_content_length": len(t.article_content) if t.article_content else 0,
                    "article_category": t.article_category,
                    "tags": t.tags or [],
                    "status": t.status,
                    "progress": getattr(t, 'progress', 100 if t.status == "completed" else 0),
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "started_at": getattr(t, 'started_at', None).isoformat() if getattr(t, 'started_at', None) else None,
                    "completed_at": getattr(t, 'completed_at', None).isoformat() if getattr(t, 'completed_at', None) else None,
                    "error_message": getattr(t, 'error_message', None),
                    "input_data": getattr(t, 'input_data', None),
                    "output_data": getattr(t, 'output_data', None)
                }
                for t in tasks
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "statistics": statistics
        }
    }


@router.get("/content/tasks/{task_id}", summary="获取任务详情")
def get_content_task_detail(task_id: int, db: Session = Depends(get_db)):
    """获取单个内容任务的详细信息（包括完整文章内容）"""
    task = db.query(ContentTask).filter(ContentTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {
        "status": "success",
        "data": {
            "id": task.id,
            "task_id": task.task_id if hasattr(task, 'task_id') else str(task.id),
            "task_type": task.task_type if hasattr(task, 'task_type') else "unknown",
            "target_platform": task.target_platform.value if hasattr(task.target_platform, 'value') else str(task.target_platform),
            "original_topic": task.original_topic,
            "article_title": task.article_title,
            "article_content": task.article_content,
            "article_category": task.article_category,
            "tags": task.tags,
            "status": task.status,
            "progress": getattr(task, 'progress', 100 if task.status == "completed" else 0),
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": getattr(task, 'started_at', None).isoformat() if getattr(task, 'started_at', None) else None,
            "completed_at": getattr(task, 'completed_at', None).isoformat() if getattr(task, 'completed_at', None) else None,
            "error_message": getattr(task, 'error_message', None),
            "input_data": getattr(task, 'input_data', None),
            "output_data": getattr(task, 'output_data', None)
        }
    }


@router.post("/content/tasks/{task_id}/retry", summary="重试任务")
def retry_task(task_id: int, db: Session = Depends(get_db)):
    """
    重试失败的任务
    
    - **task_id**: 任务ID
    """
    task = db.query(ContentTask).filter(ContentTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status != "failed":
        return {
            "status": "failed",
            "message": "只能重试失败的任务"
        }
    
    try:
        # 更新任务状态
        task.status = "pending"
        task.error_message = None
        task.progress = 0
        db.commit()
        
        logger.info(f"✅ 任务 {task_id} 已重置为待处理状态")
        
        return {
            "status": "success",
            "message": "任务已重试"
        }
    except Exception as e:
        logger.error(f"重试任务失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/content/tasks/{task_id}/cancel", summary="取消任务")
def cancel_task(task_id: int, db: Session = Depends(get_db)):
    """
    取消正在处理或待处理的任务
    
    - **task_id**: 任务ID
    """
    task = db.query(ContentTask).filter(ContentTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status not in ["pending", "processing"]:
        return {
            "status": "failed",
            "message": "只能取消待处理或处理中的任务"
        }
    
    try:
        # 更新任务状态
        task.status = "cancelled"
        task.error_message = "用户手动取消"
        db.commit()
        
        logger.info(f"✅ 任务 {task_id} 已取消")
        
        return {
            "status": "success",
            "message": "任务已取消"
        }
    except Exception as e:
        logger.error(f"取消任务失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }
