from fastapi import APIRouter, Depends

from app.api.deps import get_container, require_admin
from app.container import Container
from app.infra.db.models.user import User

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
def get_stats(c: Container = Depends(get_container),
              admin: User = Depends(require_admin)):
    return c.get_stats.execute()
