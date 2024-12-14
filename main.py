import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from database import Base, engine, get_db
from models import User, Permission, Plan, Subscription
from schemas import UserCreate, UserOut, PermissionCreate, PermissionOut, PlanCreate, PlanOut, SubscriptionCreate, SubscriptionOut, UsageOut, PlanUpdate
from crud import create_user, get_user, get_user_by_username, create_permission, modify_permission, delete_permission, create_plan, modify_plan, delete_plan, subscribe_user, get_subscription_by_user, track_usage, get_usage, get_plan
from utils import get_plan_permissions_ids
from sqlalchemy.orm import Session

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Cloud Service Access Management System")

def is_admin(db: Session, user_id: int):
    user = get_user(db, user_id)
    return user and user.role == "admin"

def check_access(db: Session, user_id: int, requested_api: str):
    sub = get_subscription_by_user(db, user_id)
    if not sub:
        return False, "No subscription found."

    plan = get_plan(db, sub.plan_id)
    if not plan:
        return False, "No plan found for user."

    permission_ids = get_plan_permissions_ids(db, plan.id)
    perms = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
    perm_map = {p.name: p for p in perms}

    if requested_api not in perm_map:
        return False, "Requested API not in plan permissions."

    usage_logs = get_usage(db, user_id)
    usage_dict = {u.permission_id: u.count for u in usage_logs}
    for p in perms:
        if p.name == requested_api:
            current_usage = usage_dict.get(p.id, 0)
            if current_usage >= plan.usage_limit:
                return False, "Usage limit reached."
            else:
                return True, "Access Granted."
    return False, "Permission not found."

# User Management
@app.post("/users", response_model=UserOut)
def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return create_user(db, user)

# Permission Management (Admin Only)
@app.post("/permissions", response_model=PermissionOut)
def add_permission(perm: PermissionCreate, admin_id: int, db: Session = Depends(get_db)):
    if not is_admin(db, admin_id):
        raise HTTPException(status_code=403, detail="Admin access required.")
    return create_permission(db, perm)

@app.put("/permissions/{permissionId}", response_model=PermissionOut)
def update_permission(permissionId: int, name: str, api_endpoint: str, description: str, admin_id: int, db: Session = Depends(get_db)):
    if not is_admin(db, admin_id):
        raise HTTPException(status_code=403, detail="Admin access required.")
    p = modify_permission(db, permissionId, name, api_endpoint, description)
    if not p:
        raise HTTPException(status_code=404, detail="Permission not found.")
    return p

@app.delete("/permissions/{permissionId}")
def remove_permission(permissionId: int, admin_id: int, db: Session = Depends(get_db)):
    if not is_admin(db, admin_id):
        raise HTTPException(status_code=403, detail="Admin access required.")
    success = delete_permission(db, permissionId)
    if not success:
        raise HTTPException(status_code=404, detail="Permission not found.")
    return {"detail": "Permission deleted"}

# Subscription Plan Management (Admin Only)
@app.post("/plans", response_model=PlanOut)
def create_subscription_plan(plan: PlanCreate, admin_id: int, db: Session = Depends(get_db)):
    if not is_admin(db, admin_id):
        raise HTTPException(status_code=403, detail="Admin access required.")
    p = create_plan(db, plan)
    # Return the plan with its permissions
    return PlanOut(id=p.id, name=p.name, description=p.description, usage_limit=p.usage_limit, permissions=[pp.permission_id for pp in p.permissions])

@app.put("/plans/{planId}", response_model=PlanOut)
def update_plan(
    planId: int,
    admin_id: int,
    plan_data: PlanUpdate,
    db: Session = Depends(get_db)
):
    p = modify_plan(
        db, 
        plan_id=planId, 
        name=plan_data.name, 
        description=plan_data.description, 
        usage_limit=plan_data.usage_limit, 
        permission_ids=plan_data.permission_ids
    )
    if not p:
        raise HTTPException(status_code=404, detail="Plan not found.")
    return PlanOut(
        id=p.id, 
        name=p.name, 
        description=p.description, 
        usage_limit=p.usage_limit, 
        permissions=[pp.permission_id for pp in p.permissions]
    )

@app.delete("/plans/{planId}")
def delete_subscription_plan(planId: int, admin_id: int, db: Session = Depends(get_db)):
    if not is_admin(db, admin_id):
        raise HTTPException(status_code=403, detail="Admin access required.")
    success = delete_plan(db, planId)
    if not success:
        raise HTTPException(status_code=404, detail="Plan not found.")
    return {"detail": "Plan deleted"}

# User Subscription Handling
@app.post("/subscriptions", response_model=SubscriptionOut)
def subscribe_to_plan(sub: SubscriptionCreate, db: Session = Depends(get_db)):
    return subscribe_user(db, sub)

@app.get("/subscriptions/{userId}", response_model=SubscriptionOut)
def view_subscription(userId: int, db: Session = Depends(get_db)):
    s = get_subscription_by_user(db, userId)
    if not s:
        raise HTTPException(status_code=404, detail="No subscription found.")
    return s

@app.get("/subscriptions/{userId}/usage", response_model=list[UsageOut])
def view_usage_statistics(userId: int, db: Session = Depends(get_db)):
    usage = get_usage(db, userId)
    return [{"permission_id": u.permission_id, "count": u.count} for u in usage]

@app.put("/subscriptions/{userId}", response_model=SubscriptionOut)
def assign_modify_user_plan(userId: int, plan_id: int, admin_id: int, db: Session = Depends(get_db)):
    if not is_admin(db, admin_id):
        raise HTTPException(status_code=403, detail="Admin access required.")
    sub = SubscriptionCreate(user_id=userId, plan_id=plan_id)
    return subscribe_user(db, sub)

# Access Control
@app.get("/access/{userId}/{apiRequest}")
def check_access_permission(userId: int, apiRequest: str, db: Session = Depends(get_db)):
    allowed, msg = check_access(db, userId, apiRequest)
    if allowed:
        return {"detail": msg}
    else:
        raise HTTPException(status_code=403, detail=msg)

# Usage Tracking and Limit Enforcement
@app.post("/usage/{userId}")
def track_api_request(userId: int, api_name: str, db: Session = Depends(get_db)):
    allowed, msg = check_access(db, userId, api_name)
    if not allowed:
        raise HTTPException(status_code=403, detail=msg)
    sub = get_subscription_by_user(db, userId)
    plan = get_plan(db, sub.plan_id)
    permission_ids = get_plan_permissions_ids(db, plan.id)
    perms = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
    perm_map = {p.name:p.id for p in perms}
    if api_name not in perm_map:
        raise HTTPException(status_code=404, detail="Permission not found.")

    track_usage(db, userId, perm_map[api_name])
    return {"detail": "Usage recorded"}

@app.get("/usage/{userId}/limit")
def check_limit_status(userId: int, db: Session = Depends(get_db)):
    sub = get_subscription_by_user(db, userId)
    if not sub:
        raise HTTPException(status_code=404, detail="No subscription found.")
    plan = get_plan(db, sub.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="No plan found.")
    usage = get_usage(db, userId)
    usage_sum = sum(u.count for u in usage)
    return {"usage": usage_sum, "limit": plan.usage_limit}


# The 6 Random Cloud Service APIs
@app.get("/service1")
def service1():
    return {"detail": "This is Cloud Service 1"}

@app.get("/service2")
def service2():
    return {"detail": "This is Cloud Service 2"}

@app.get("/service3")
def service3():
    return {"detail": "This is Cloud Service 3"}

@app.get("/service4")
def service4():
    return {"detail": "This is Cloud Service 4"}

@app.get("/service5")
def service5():
    return {"detail": "This is Cloud Service 5"}

@app.get("/service6")
def service6():
    return {"detail": "This is Cloud Service 6"}
