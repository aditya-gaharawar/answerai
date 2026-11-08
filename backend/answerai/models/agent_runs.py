"""Persistent, owner-scoped agent executions with fenced worker leases."""

from answerai.internal.db import Base
from sqlalchemy import JSON, BigInteger, Column, Integer, String, Text, UniqueConstraint


class AgentRun(Base):
    __tablename__ = 'agent_run'
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    request_key = Column(String, nullable=False)
    chat_id = Column(String, nullable=False)
    message_id = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)
    model_id = Column(String, nullable=False)
    status = Column(String, nullable=False, index=True)
    checkpoint = Column(JSON, nullable=False)
    options = Column(JSON, nullable=False, default=dict)
    timeline = Column(JSON, nullable=False, default=list)
    event_sequence = Column(Integer, nullable=False, default=0)
    token_budget = Column(Integer, nullable=False, default=256000)
    tokens_used = Column(Integer, nullable=False, default=0)
    lease = Column(String, nullable=True)
    lease_until = Column(BigInteger, nullable=False, default=0)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)
    deadline = Column(BigInteger, nullable=False)
    iterations = Column(Integer, nullable=False)
    max_seconds = Column(Integer, nullable=False, default=300)
    resume_count = Column(Integer, nullable=False, default=0)
    __table_args__ = (UniqueConstraint('user_id', 'request_key', name='uq_agent_run_request'),)


class AgentOwnerLease(Base):
    __tablename__ = 'agent_owner_lease'
    user_id = Column(String, primary_key=True)
    run_id = Column(String, nullable=False)
    lease = Column(String, nullable=False)
    lease_until = Column(BigInteger, nullable=False)
