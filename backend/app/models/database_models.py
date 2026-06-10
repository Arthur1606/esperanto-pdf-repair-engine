from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from language_engine.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, index=True)
    status = Column(String, default="pending")  # auditing, pending_review, correcting, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    documents = relationship("Document", back_populates="project")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"))
    filename = Column(String)
    status = Column(String, default="uploaded")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Quality Scores
    unicode_score = Column(Float, nullable=True)
    font_score = Column(Float, nullable=True)
    text_validity_score = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=True)
    
    # URLs to local files
    original_file_path = Column(String)
    corrected_file_path = Column(String, nullable=True)
    reviewed_file_path = Column(String, nullable=True)
    
    debug_info = Column(JSON, nullable=True)
    
    project = relationship("Project", back_populates="documents")
    fonts = relationship("FontAudit", back_populates="document", cascade="all, delete-orphan")
    corrections = relationship("CorrectionHistory", back_populates="document", cascade="all, delete-orphan")

class FontAudit(Base):
    __tablename__ = "font_audits"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id"))
    font_name = Column(String)
    page_count = Column(Integer)
    unicode_support = Column(Boolean)
    esperanto_support = Column(Boolean)
    
    document = relationship("Document", back_populates="fonts")

class CorrectionHistory(Base):
    __tablename__ = "correction_history"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id"))
    page_num = Column(Integer)
    
    original_string = Column(String)
    suggested_string = Column(String)
    confidence = Column(Float)
    status = Column(String, default="pending") # pending, accepted, rejected, auto_applied
    error_type = Column(String) # encoding, x_system, suspicious_word
    
    # Bounding Box can be stored as JSON: {"x0": 0.0, "y0": 0.0, "x1": 0.0, "y1": 0.0}
    bounding_box = Column(JSON, nullable=True)
    
    document = relationship("Document", back_populates="corrections")
