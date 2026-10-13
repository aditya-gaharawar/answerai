"""Durable entitlements, usage counters, subscriptions, and active-call leases."""

from answerai.internal.db import Base
from sqlalchemy import BigInteger, Boolean, Column, Integer, String


class BillingAccount(Base):
    __tablename__ = 'billing_account'
    user_id = Column(String, primary_key=True)
    override = Column(String, nullable=False, default='')
    override_until = Column(BigInteger, nullable=False, default=0)
    checkout_until = Column(BigInteger, nullable=False, default=0)


class Subscription(Base):
    __tablename__ = 'billing_subscription'
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    provider = Column(String, nullable=False)
    checkout_id = Column(String, nullable=True, unique=True)
    provider_id = Column(String, nullable=True, unique=True)
    status = Column(String, nullable=False, default='pending')
    period_end = Column(BigInteger, nullable=False, default=0)
    cancel_at_period_end = Column(Boolean, nullable=False, default=False)
    created_at = Column(BigInteger, nullable=False)
    reconciled_at = Column(BigInteger, nullable=False, default=0)


class BillingEvent(Base):
    __tablename__ = 'billing_event'
    id = Column(String, primary_key=True)
    created_at = Column(BigInteger, nullable=False)


class UsageBucket(Base):
    __tablename__ = 'billing_usage'
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    metric = Column(String, nullable=False)
    window = Column(Integer, nullable=False)
    starts_at = Column(BigInteger, nullable=False, index=True)
    used = Column(Integer, nullable=False, default=0)


class LiveLease(Base):
    __tablename__ = 'live_lease'
    user_id = Column(String, primary_key=True)
    session_id = Column(String, nullable=False)
    expires_at = Column(BigInteger, nullable=False)
