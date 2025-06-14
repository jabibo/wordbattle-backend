from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, text
from typing import Optional, List
import uuid
from datetime import datetime
import json

from ..db import get_db
from ..auth import get_current_user
from ..models.feedback import Feedback, FeedbackCategory as DBFeedbackCategory, FeedbackStatus as DBFeedbackStatus
from ..schemas.feedback import (
    FeedbackSubmissionRequest, FeedbackSubmissionResponse,
    FeedbackListResponse, FeedbackDetailsResponse,
    FeedbackStatusUpdateRequest, FeedbackStatusUpdateResponse,
    FeedbackCategory, FeedbackStatus, FeedbackSummary, UserInfo,
    DebugLogEntry, DeviceInfo, AppInfo
)

router = APIRouter(prefix="/feedback", tags=["feedback"])

def convert_to_json_serializable(obj):
    """Convert Pydantic models and enums to JSON-serializable format"""
    if hasattr(obj, 'dict'):
        # It's a Pydantic model
        data = obj.dict()
        # Convert any enum values and datetime objects to their string representation
        for key, value in data.items():
            if hasattr(value, 'value'):
                data[key] = value.value
            elif isinstance(value, datetime):
                data[key] = value.isoformat()
        return data
    elif hasattr(obj, 'value'):
        # It's an enum
        return obj.value
    elif isinstance(obj, datetime):
        # It's a datetime object
        return obj.isoformat()
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    else:
        return obj

@router.post("/submit", response_model=FeedbackSubmissionResponse)
def submit_feedback(
    feedback_data: FeedbackSubmissionRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit user feedback with debug logs"""
    try:
        # Generate unique feedback ID
        feedback_id = str(uuid.uuid4())
        
        # Convert Pydantic models to dict for JSON storage
        debug_logs_json = None
        if feedback_data.debug_logs:
            debug_logs_json = [convert_to_json_serializable(log) for log in feedback_data.debug_logs]
        
        device_info_json = None
        if feedback_data.device_info:
            device_info_json = convert_to_json_serializable(feedback_data.device_info)
        
        app_info_json = None
        if feedback_data.app_info:
            app_info_json = convert_to_json_serializable(feedback_data.app_info)
        
        # Create feedback record with string values for enum fields
        feedback = Feedback(
            id=feedback_id,
            user_id=current_user.id,
            category=feedback_data.category.value,
            description=feedback_data.description,
            contact_email=feedback_data.email,
            debug_logs=debug_logs_json,
            device_info=device_info_json,
            app_info=app_info_json,
            status="new",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        
        return FeedbackSubmissionResponse(
            success=True,
            feedback_id=feedback_id,
            message="Feedback submitted successfully. Thank you for helping us improve WordBattle!",
            created_at=feedback.created_at
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")

@router.get("/list", response_model=FeedbackListResponse)
def list_feedback(
    category: Optional[FeedbackCategory] = Query(None),
    status: Optional[FeedbackStatus] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List feedback submissions (admin only)"""
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Build query conditions
        conditions = []
        if category:
            conditions.append(Feedback.category == category.value)
        if status:
            conditions.append(Feedback.status == status.value)
        
        # Get total count
        count_query = db.query(func.count(Feedback.id))
        if conditions:
            count_query = count_query.filter(and_(*conditions))
        
        total_count = count_query.scalar()
        
        # Get feedback list with user info
        query = db.query(Feedback).order_by(Feedback.created_at.desc())
        if conditions:
            query = query.filter(and_(*conditions))
        query = query.offset(offset).limit(limit)
        
        feedback_list = query.all()
        
        # Convert to response format
        feedback_summaries = []
        for feedback in feedback_list:
            # Get user info (assuming we have access to user data)
            user_info = UserInfo(
                user_id=str(feedback.user_id),  # Convert to string
                username=None,  # Would need to join with users table
                email=None      # Would need to join with users table
            )
            
            # Create description preview (first 100 characters)
            description_preview = feedback.description[:100]
            if len(feedback.description) > 100:
                description_preview += "..."
            
            # Count debug logs
            debug_logs_count = 0
            if feedback.debug_logs:
                debug_logs_count = len(feedback.debug_logs)
            
            feedback_summaries.append(FeedbackSummary(
                feedback_id=feedback.id,
                category=FeedbackCategory(feedback.category),
                description_preview=description_preview,
                status=FeedbackStatus(feedback.status),
                submitted_at=feedback.created_at,
                user_info=user_info,
                debug_logs_count=debug_logs_count
            ))
        
        has_more = (offset + limit) < total_count
        
        return FeedbackListResponse(
            feedback_submissions=feedback_summaries,
            total_count=total_count,
            has_more=has_more
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list feedback: {str(e)}")

@router.get("/{feedback_id}", response_model=FeedbackDetailsResponse)
def get_feedback_details(
    feedback_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed feedback with debug logs (admin only)"""
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get feedback by ID using ORM
        feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
        
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found")
        
        # Get user info (assuming we have access to user data)
        user_info = UserInfo(
            user_id=str(feedback.user_id),  # Convert to string
            username=None,  # Would need to join with users table
            email=None      # Would need to join with users table
        )
        
        # Convert debug logs back to Pydantic models
        debug_logs = None
        if feedback.debug_logs:
            debug_logs = [DebugLogEntry(**log) for log in feedback.debug_logs]
        
        # Convert device info back to Pydantic model
        device_info = None
        if feedback.device_info:
            device_info = DeviceInfo(**feedback.device_info)
        
        # Convert app info back to Pydantic model
        app_info = None
        if feedback.app_info:
            app_info = AppInfo(**feedback.app_info)
        
        return FeedbackDetailsResponse(
            feedback_id=feedback.id,
            category=FeedbackCategory(feedback.category),
            description=feedback.description,
            contact_email=feedback.contact_email,
            status=FeedbackStatus(feedback.status),
            submitted_at=feedback.created_at,
            updated_at=feedback.updated_at,
            user_info=user_info,
            debug_logs=debug_logs,
            device_info=device_info,
            app_info=app_info,
            admin_notes=feedback.admin_notes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get feedback details: {str(e)}")

@router.patch("/{feedback_id}", response_model=FeedbackStatusUpdateResponse)
def update_feedback_status(
    feedback_id: str,
    update_data: FeedbackStatusUpdateRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update feedback status (admin only)"""
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get feedback by ID using ORM
        feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found")
        
        # Update feedback
        feedback.status = update_data.status.value
        if update_data.admin_notes:
            feedback.admin_notes = update_data.admin_notes
        feedback.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(feedback)
        
        return FeedbackStatusUpdateResponse(
            success=True,
            feedback_id=feedback_id,
            new_status=FeedbackStatus(update_data.status.value),
            updated_at=feedback.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update feedback status: {str(e)}") 