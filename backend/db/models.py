import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, String, Text, ForeignKey, Integer, Enum, Index, JSON, TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
import enum

from backend.db.database import Base


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value) if not isinstance(value, uuid.UUID) else value
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            else:
                return value


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    TRIAL = "trial"


class User(Base):
    __tablename__ = "users"

    user_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)

    # Telegram fields
    telegram_id = Column(Integer, unique=True, index=True, nullable=True)
    telegram_username = Column(String(255), nullable=True)
    telegram_first_name = Column(String(255), nullable=True)
    telegram_last_name = Column(String(255), nullable=True)
    telegram_language_code = Column(String(10), nullable=True)

    is_active = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False)
    subscription_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False)
    subscription_start_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    subscription_end_date = Column(DateTime, nullable=True)
    trial_end_date = Column(DateTime, nullable=True)

    # User preferences
    preferred_language = Column(String(2), default="fr", nullable=False)  # 'fr' or 'en'

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Email verification
    verification_token = Column(String(255), nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)

    # Password reset
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)

    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class Conversation(Base):
    __tablename__ = "conversations"

    conversation_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.user_id"), nullable=False)

    title = Column(String(255), nullable=True)

    is_archived = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Conversation {self.conversation_id} - {self.title}>"


class Message(Base):
    __tablename__ = "messages"

    message_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    conversation_id = Column(GUID, ForeignKey("conversations.conversation_id"), nullable=False)

    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)

    # Metadata
    intent = Column(String(100), nullable=True)
    tools_used = Column(Text, nullable=True)  # JSON string of tools used

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message {self.message_id} - {self.role}>"


class MatchAnalysis(Base):
    __tablename__ = "match_analyses"

    # Clé primaire
    analysis_id = Column(GUID, primary_key=True, default=uuid.uuid4)

    # Identification du match
    fixture_id = Column(Integer, unique=True, nullable=False, index=True)

    # Informations du match (pour requêtes rapides sans JOIN)
    home_team = Column(String(255), nullable=False)
    away_team = Column(String(255), nullable=False)
    league = Column(String(255), nullable=False)
    season = Column(Integer, nullable=False)
    match_date = Column(DateTime, nullable=False)

    # Statut actuel (pour détecter les changements)
    match_status = Column(String(10), nullable=False)  # NS, FT, 1H, etc.

    # Analyses (JSON)
    # Stocke les 8 types : {"1x2": {...}, "goals": {...}, ...}
    analyses_data = Column(JSON, nullable=False)

    # Métadonnées
    api_calls_count = Column(Integer, default=0)
    version = Column(String(10), default="2.0")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_accessed = Column(DateTime, nullable=True)
    access_count = Column(Integer, default=0)

    # Index composé pour recherches fréquentes
    __table_args__ = (
        Index('idx_match_status_date', 'match_status', 'match_date'),
        Index('idx_fixture_id', 'fixture_id'),
        Index('idx_match_date', 'match_date'),
    )

    def __repr__(self):
        return f"<MatchAnalysis {self.fixture_id} - {self.home_team} vs {self.away_team}>"


class MatchAnalysisAccess(Base):
    __tablename__ = "match_analysis_accesses"

    access_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    analysis_id = Column(GUID, ForeignKey("match_analyses.analysis_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(GUID, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    conversation_id = Column(GUID, ForeignKey("conversations.conversation_id", ondelete="SET NULL"), nullable=True)
    accessed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    match_analysis = relationship("MatchAnalysis")
    user = relationship("User")
    conversation = relationship("Conversation")

    def __repr__(self):
        return f"<MatchAnalysisAccess {self.access_id} - {self.accessed_at}>"
