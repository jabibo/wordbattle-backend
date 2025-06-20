from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class FeedbackCategory(str, Enum):
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    GAMEPLAY_ISSUE = "gameplay_issue"
    PERFORMANCE_ISSUE = "performance_issue"
    UI_UX_FEEDBACK = "ui_ux_feedback"
    CONTENT_SUGGESTION = "content_suggestion"
    TECHNICAL_SUPPORT = "technical_support"
    ACCOUNT_ISSUE = "account_issue"
    OTHER = "other"

class FeedbackStatus(str, Enum):
    NEW = "new"
    RESOLVED = "resolved"
    CLOSED = "closed"

class DebugLogCategory(str, Enum):
    AUTH = "AUTH"
    GAME = "GAME"
    WEBSOCKET = "WEBSOCKET"
    NETWORK = "NETWORK"
    UI = "UI"
    FEEDBACK = "FEEDBACK"
    DEBUG_LOGGER = "DEBUG_LOGGER"
    MAIN = "MAIN"

class Platform(str, Enum):
    IOS = "iOS"
    ANDROID = "Android"

class Environment(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"

class DebugLogEntry(BaseModel):
    timestamp: datetime
    category: DebugLogCategory
    message: str
    metadata: Optional[Dict[str, Any]] = None

class DeviceInfo(BaseModel):
    platform: Optional[Platform] = None
    device_model: Optional[str] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None
    build_number: Optional[str] = None
    screen_size: Optional[str] = None
    locale: Optional[str] = None

class AppInfo(BaseModel):
    version: Optional[str] = None
    build_number: Optional[str] = None
    environment: Optional[Environment] = None
    backend_url: Optional[str] = None

class FeedbackSubmissionRequest(BaseModel):
    category: FeedbackCategory
    description: str = Field(..., min_length=10, max_length=2000)
    email: Optional[EmailStr] = None
    debug_logs: Optional[List[DebugLogEntry]] = None
    device_info: Optional[DeviceInfo] = None
    app_info: Optional[AppInfo] = None

class FeedbackSubmissionResponse(BaseModel):
    success: bool
    feedback_id: str
    message: Optional[str] = None
    created_at: datetime

class UserInfo(BaseModel):
    user_id: str
    username: Optional[str] = None
    email: Optional[str] = None

class FeedbackSummary(BaseModel):
    feedback_id: str
    category: FeedbackCategory
    description_preview: str
    status: FeedbackStatus
    submitted_at: datetime
    user_info: UserInfo
    debug_logs_count: int

class FeedbackListResponse(BaseModel):
    feedback_submissions: List[FeedbackSummary]
    total_count: int
    has_more: bool

class FeedbackDetailsResponse(BaseModel):
    feedback_id: str
    category: FeedbackCategory
    description: str
    contact_email: Optional[str] = None
    status: FeedbackStatus
    submitted_at: datetime
    updated_at: datetime
    user_info: UserInfo
    debug_logs: Optional[List[DebugLogEntry]] = None
    device_info: Optional[DeviceInfo] = None
    app_info: Optional[AppInfo] = None
    admin_notes: Optional[str] = None

class FeedbackStatusUpdateRequest(BaseModel):
    status: FeedbackStatus
    admin_notes: Optional[str] = Field(None, max_length=1000)

class FeedbackStatusUpdateResponse(BaseModel):
    success: bool
    feedback_id: str
    new_status: FeedbackStatus
    updated_at: datetime 