from pydantic import BaseModel
from typing import List, Optional
from pydantic import BaseModel

# User schemas
class UserCreate(BaseModel):
    username: str
    role: str

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    class Config:
        orm_mode = True

# Permission schemas
class PermissionCreate(BaseModel):
    name: str
    api_endpoint: str
    description: str

class PermissionOut(BaseModel):
    id: int
    name: str
    api_endpoint: str
    description: str
    class Config:
        orm_mode = True

# Plan schemas
class PlanCreate(BaseModel):
    name: str
    description: str
    usage_limit: int
    permission_ids: List[int]

class PlanOut(BaseModel):
    id: int
    name: str
    description: str
    usage_limit: int
    permissions: List[int]
    class Config:
        orm_mode = True

class PlanUpdate(BaseModel):
    name: str
    description: str
    usage_limit: int
    permission_ids: List[int]

# Subscription schemas
class SubscriptionCreate(BaseModel):
    user_id: int
    plan_id: int

class SubscriptionOut(BaseModel):
    id: int
    user_id: int
    plan_id: int
    class Config:
        orm_mode = True

# Usage schemas
class UsageOut(BaseModel):
    permission_id: int
    count: int
