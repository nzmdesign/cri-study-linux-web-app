from datetime import datetime

from fastapi import APIRouter


router = APIRouter()


@router.get("/health")
def health_check():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }
