from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from .connection import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, index=True)
    jd_text = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="processing")
    total_cvs = Column(Integer, nullable=False)
    successful_cvs = Column(Integer, default=0)
    failed_cvs = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    correlation_id = Column(String(36), nullable=True)
    cv_analyses = relationship("CVAnalysis", back_populates="job", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_jobs_status_created', 'status', 'created_at'),
        Index('ix_jobs_correlation_id', 'correlation_id'),
    )
    def __repr__(self):
        return f"<Job(id={self.id}, status={self.status}, cvs={self.successful_cvs}/{self.total_cvs})>"


class CVAnalysis(Base):
    __tablename__ = "cv_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    cv_id = Column(String(36), nullable=False)
    original_filename = Column(String(255), nullable=False)
    candidate_name = Column(String(255), nullable=False)
    match_score = Column(Integer, nullable=False)
    summary_headline = Column(Text, nullable=False)
    conceptual_matches = Column(JSON, nullable=False)
    skill_gaps = Column(JSON, nullable=False)
    experience_analysis = Column(Text, nullable=False)
    recommendation = Column(String(50), nullable=False)
    risk_assessment = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    portfolio_url = Column(String(500), nullable=True)
    
    analyzed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    job = relationship("Job", back_populates="cv_analyses")
    
    __table_args__ = (
        Index('ix_cv_analyses_job_id', 'job_id'),
        Index('ix_cv_analyses_cv_id', 'cv_id'),
        Index('ix_cv_analyses_match_score', 'match_score'),
        Index('ix_cv_analyses_recommendation', 'recommendation'),
    )
    
    def __repr__(self):
        return f"<CVAnalysis(cv_id={self.cv_id}, candidate={self.candidate_name}, score={self.match_score})>"
