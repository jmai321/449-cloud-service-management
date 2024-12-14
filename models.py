
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    role = Column(String, default="customer")  # either "admin" or "customer"

    subscription = relationship("Subscription", back_populates="user", uselist=False)


class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    api_endpoint = Column(String)
    description = Column(String)


class Plan(Base):
    __tablename__ = "plans"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    usage_limit = Column(Integer)
    permissions = relationship("PlanPermission", back_populates="plan")


class PlanPermission(Base):
    __tablename__ = "plan_permissions"
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"))
    permission_id = Column(Integer, ForeignKey("permissions.id"))

    plan = relationship("Plan", back_populates="permissions")
    permission = relationship("Permission")


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_id = Column(Integer, ForeignKey("plans.id"))

    user = relationship("User", back_populates="subscription")
    plan = relationship("Plan")


class UsageLog(Base):
    __tablename__ = "usage_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    permission_id = Column(Integer, ForeignKey("permissions.id"))
    count = Column(Integer, default=0)
