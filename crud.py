from sqlalchemy.orm import Session
from models import User, Permission, Plan, Subscription, PlanPermission, UsageLog
from schemas import UserCreate, PermissionCreate, PlanCreate, SubscriptionCreate

def create_user(db: Session, user: UserCreate):
    db_user = User(username=user.username, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_permission(db: Session, permission: PermissionCreate):
    db_perm = Permission(**permission.dict())
    db.add(db_perm)
    db.commit()
    db.refresh(db_perm)
    return db_perm

def get_permission(db: Session, perm_id: int):
    return db.query(Permission).filter(Permission.id == perm_id).first()

def delete_permission(db: Session, perm_id: int):
    db_perm = get_permission(db, perm_id)
    if db_perm:
        db.delete(db_perm)
        db.commit()
        return True
    return False

def modify_permission(db: Session, perm_id: int, name: str, api_endpoint: str, description: str):
    db_perm = get_permission(db, perm_id)
    if db_perm:
        db_perm.name = name
        db_perm.api_endpoint = api_endpoint
        db_perm.description = description
        db.commit()
        db.refresh(db_perm)
        return db_perm
    return None

def create_plan(db: Session, plan: PlanCreate):
    db_plan = Plan(name=plan.name, description=plan.description, usage_limit=plan.usage_limit)
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    # Add permissions
    for perm_id in plan.permission_ids:
        pp = PlanPermission(plan_id=db_plan.id, permission_id=perm_id)
        db.add(pp)
    db.commit()
    return db_plan

def get_plan(db: Session, plan_id: int):
    return db.query(Plan).filter(Plan.id == plan_id).first()

def modify_plan(db: Session, plan_id: int, name: str, description: str, usage_limit: int, permission_ids: list):
    db_plan = get_plan(db, plan_id)
    if db_plan:
        db_plan.name = name
        db_plan.description = description
        db_plan.usage_limit = usage_limit
        for pp in db_plan.permissions:
            db.delete(pp)
        db.commit()
        for pid in permission_ids:
            pp = PlanPermission(plan_id=db_plan.id, permission_id=pid)
            db.add(pp)
        db.commit()
        db.refresh(db_plan)
        return db_plan
    return None

def delete_plan(db: Session, plan_id: int):
    db_plan = get_plan(db, plan_id)
    if db_plan:
        for pp in db_plan.permissions:
            db.delete(pp)
        db.delete(db_plan)
        db.commit()
        return True
    return False

def subscribe_user(db: Session, subscription: SubscriptionCreate):
    db_sub = db.query(Subscription).filter(Subscription.user_id == subscription.user_id).first()
    if db_sub:
        db_sub.plan_id = subscription.plan_id
        db.commit()
        db.refresh(db_sub)
        return db_sub
    else:
        db_sub = Subscription(user_id=subscription.user_id, plan_id=subscription.plan_id)
        db.add(db_sub)
        db.commit()
        db.refresh(db_sub)
        return db_sub

def get_subscription_by_user(db: Session, user_id: int):
    return db.query(Subscription).filter(Subscription.user_id == user_id).first()

def track_usage(db: Session, user_id: int, permission_id: int):
    usage = db.query(UsageLog).filter(UsageLog.user_id == user_id, UsageLog.permission_id == permission_id).first()
    if not usage:
        usage = UsageLog(user_id=user_id, permission_id=permission_id, count=1)
        db.add(usage)
    else:
        usage.count += 1
    db.commit()
    db.refresh(usage)
    return usage

def get_usage(db: Session, user_id: int):
    return db.query(UsageLog).filter(UsageLog.user_id == user_id).all()
