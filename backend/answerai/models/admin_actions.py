"""Minimal, secret-free records of privileged account and security changes."""

from answerai.internal.db import Base
from sqlalchemy import JSON, BigInteger, Column, String


class AdminAction(Base):
    __tablename__ = 'admin_action'
    id = Column(String, primary_key=True)
    actor_id = Column(String, nullable=False)
    target_id = Column(String, nullable=True)
    action = Column(String, nullable=False)
    details = Column(JSON, nullable=False)
    created_at = Column(BigInteger, nullable=False, index=True)
