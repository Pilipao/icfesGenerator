from sqlalchemy import Column, String, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.types import UserDefinedType
from core.database import Base
import uuid

# Define Vector type for SQLAlchemy if not available directly
class Vector(UserDefinedType):
    def get_col_spec(self, **kw):
        return "VECTOR(1536)"

class RagDocument(Base):
    __tablename__ = "rag_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_type = Column(String, nullable=False)
    exam = Column(String)
    skill = Column(String)
    topic = Column(String)
    difficulty_band = Column(String)
    content = Column(Text, nullable=False)
    metadata_ = Column("metadata", JSONB, default={})
    source_file = Column(String)
    embedding = Column(Vector)

class ItemsBank(Base):
    __tablename__ = "items_bank"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam = Column(String)
    skill = Column(String)
    difficulty = Column(String)
    question_content = Column(JSONB, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    status = Column(String, default="draft")

class SimilarityItem(Base):
    __tablename__ = "similarity_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_hash = Column(String)
    content_snippet = Column(Text)
    embedding = Column(Vector)
    source = Column(String)
