"""One active, hashed email verification token per account."""

from answerai.internal.db import Base
from sqlalchemy import BigInteger, Column, String


class EmailVerification(Base):
    __tablename__ = 'email_verification'

    user_id = Column(String, primary_key=True)
    email = Column(String, nullable=False)
    token_hash = Column(String(64), nullable=True, unique=True)
    expires_at = Column(BigInteger, nullable=False)
    sent_at = Column(BigInteger, nullable=False)
