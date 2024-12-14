
from typing import List
from sqlalchemy.orm import Session
from models import Plan, Permission

def get_plan_permissions_ids(db: Session, plan_id: int) -> List[int]:
    db_plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if db_plan:
        return [pp.permission_id for pp in db_plan.permissions]
    return []
