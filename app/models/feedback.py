from sqlalchemy import Column, String, Text, DateTime, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM
from datetime import datetime
import enum
from app.database import Base

class FeedbackCategory(enum.Enum):
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    GAMEPLAY_ISSUE = "gameplay_issue"
    PERFORMANCE_ISSUE = "performance_issue"
    UI_UX_FEEDBACK = "ui_ux_feedback"
    CONTENT_SUGGESTION = "content_suggestion"
    TECHNICAL_SUPPORT = "technical_support"
    ACCOUNT_ISSUE = "account_issue"
    OTHER = "other"

class FeedbackStatus(enum.Enum):
    NEW = "new"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    CLOSED = "closed"

# Create PostgreSQL enum types
feedback_category_enum = ENUM(
    'bug_report', 'feature_request', 'gameplay_issue', 
    'performance_issue', 'ui_ux_feedback', 'content_suggestion',
    'technical_support', 'account_issue', 'other',
    name='feedbackcategory'
)

feedback_status_enum = ENUM(
    'new', 'in_review', 'resolved', 'closed',
    name='feedbackstatus'
)

class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(feedback_category_enum, nullable=False)
    description = Column(Text, nullable=False)
    contact_email = Column(String, nullable=True)
    status = Column(feedback_status_enum, default="new", nullable=False)
    debug_logs = Column(JSON, nullable=True)  # Array of debug log entries
    device_info = Column(JSON, nullable=True)  # Device information
    app_info = Column(JSON, nullable=True)  # App information
    admin_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship to user (will be added to User model separately)
    # user = relationship("User", back_populates="feedback_submissions") 