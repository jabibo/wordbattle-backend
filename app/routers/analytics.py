from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from app.auth import get_current_user
from app.models.user import User
import logging
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    responses={404: {"description": "Not found"}},
)

# In-memory storage for performance metrics (in production, use a proper database)
performance_metrics = []
performance_stats = defaultdict(list)

class PerformanceMetric(BaseModel):
    """Performance metric data from frontend telemetry"""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metric_type: str = Field(..., description="Type of performance metric (e.g., 'token_refresh', 'api_call', 'websocket_reconnect')")
    metric_name: str = Field(..., description="Specific name of the metric")
    duration_ms: Optional[float] = Field(None, description="Duration in milliseconds")
    value: Optional[float] = Field(None, description="Metric value")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PerformanceMetricBatch(BaseModel):
    """Batch of performance metrics for efficient submission"""
    metrics: List[PerformanceMetric]
    client_info: Optional[Dict[str, Any]] = Field(default_factory=dict)

class PerformanceAnalytics(BaseModel):
    """Performance analytics response"""
    total_metrics: int
    time_range: Dict[str, datetime]
    metric_types: Dict[str, int]
    avg_durations: Dict[str, float]
    slowest_operations: List[Dict[str, Any]]
    performance_issues: List[Dict[str, Any]]

@router.post("/performance", response_model=Dict[str, Any])
async def submit_performance_metrics(
    batch: PerformanceMetricBatch,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Submit performance metrics from frontend telemetry service.
    
    This endpoint receives performance data from the frontend to help identify
    bottlenecks and optimize user experience.
    """
    try:
        # Add user context to metrics
        processed_metrics = []
        for metric in batch.metrics:
            metric.user_id = str(current_user.id)
            
            # Store in memory (in production, use proper database)
            performance_metrics.append(metric.dict())
            performance_stats[metric.metric_type].append({
                "duration_ms": metric.duration_ms,
                "value": metric.value,
                "timestamp": metric.timestamp,
                "metadata": metric.metadata
            })
            
            processed_metrics.append(metric.dict())
        
        # Log performance issues for immediate attention
        for metric in batch.metrics:
            if metric.metric_type == "token_refresh" and metric.duration_ms and metric.duration_ms > 500:
                logger.warning(f"Slow token refresh detected: {metric.duration_ms}ms for user {current_user.username}")
            elif metric.metric_type == "api_call" and metric.duration_ms and metric.duration_ms > 2000:
                logger.warning(f"Slow API call detected: {metric.metric_name} took {metric.duration_ms}ms for user {current_user.username}")
            elif metric.metric_type == "websocket_reconnect":
                logger.info(f"WebSocket reconnection logged for user {current_user.username}: {metric.metadata}")
        
        logger.info(f"Received {len(batch.metrics)} performance metrics from user {current_user.username}")
        
        return {
            "success": True,
            "message": f"Successfully recorded {len(batch.metrics)} performance metrics",
            "metrics_processed": len(processed_metrics),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to process performance metrics")

@router.get("/performance", response_model=PerformanceAnalytics)
async def get_performance_analytics(
    metric_type: Optional[str] = None,
    hours: int = 24,
    current_user: User = Depends(get_current_user)
):
    """
    Get performance analytics and insights.
    
    Returns aggregated performance data to help identify bottlenecks and trends.
    """
    try:
        # Filter metrics by time range
        cutoff_time = datetime.now(timezone.utc).replace(hour=datetime.now().hour - hours)
        
        # Filter metrics
        filtered_metrics = []
        for metric in performance_metrics:
            metric_time = datetime.fromisoformat(metric['timestamp'].replace('Z', '+00:00'))
            if metric_time >= cutoff_time:
                if not metric_type or metric['metric_type'] == metric_type:
                    filtered_metrics.append(metric)
        
        # Calculate analytics
        total_metrics = len(filtered_metrics)
        metric_types = defaultdict(int)
        durations_by_type = defaultdict(list)
        
        for metric in filtered_metrics:
            metric_types[metric['metric_type']] += 1
            if metric.get('duration_ms'):
                durations_by_type[metric['metric_type']].append(metric['duration_ms'])
        
        # Calculate average durations
        avg_durations = {}
        for mtype, durations in durations_by_type.items():
            if durations:
                avg_durations[mtype] = sum(durations) / len(durations)
        
        # Find slowest operations
        slowest_operations = []
        for metric in filtered_metrics:
            if metric.get('duration_ms') and metric['duration_ms'] > 1000:  # Slower than 1 second
                slowest_operations.append({
                    "metric_type": metric['metric_type'],
                    "metric_name": metric['metric_name'],
                    "duration_ms": metric['duration_ms'],
                    "timestamp": metric['timestamp'],
                    "user_id": metric.get('user_id')
                })
        
        # Sort by duration
        slowest_operations.sort(key=lambda x: x['duration_ms'], reverse=True)
        slowest_operations = slowest_operations[:10]  # Top 10 slowest
        
        # Identify performance issues
        performance_issues = []
        
        # Token refresh issues
        token_refresh_times = durations_by_type.get('token_refresh', [])
        if token_refresh_times:
            avg_token_refresh = sum(token_refresh_times) / len(token_refresh_times)
            if avg_token_refresh > 500:
                performance_issues.append({
                    "issue": "slow_token_refresh",
                    "description": f"Average token refresh time is {avg_token_refresh:.1f}ms (target: <500ms)",
                    "severity": "high" if avg_token_refresh > 1000 else "medium",
                    "count": len(token_refresh_times)
                })
        
        # WebSocket reconnection issues
        websocket_reconnects = metric_types.get('websocket_reconnect', 0)
        if websocket_reconnects > 5:  # More than 5 reconnects in time period
            performance_issues.append({
                "issue": "frequent_websocket_reconnects",
                "description": f"{websocket_reconnects} WebSocket reconnections detected",
                "severity": "medium",
                "count": websocket_reconnects
            })
        
        # Calculate time range
        time_range = {}
        if filtered_metrics:
            timestamps = [datetime.fromisoformat(m['timestamp'].replace('Z', '+00:00')) for m in filtered_metrics]
            time_range = {
                "start": min(timestamps),
                "end": max(timestamps)
            }
        
        return PerformanceAnalytics(
            total_metrics=total_metrics,
            time_range=time_range,
            metric_types=dict(metric_types),
            avg_durations=avg_durations,
            slowest_operations=slowest_operations,
            performance_issues=performance_issues
        )
        
    except Exception as e:
        logger.error(f"Error getting performance analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance analytics")

@router.get("/performance/summary")
async def get_performance_summary(current_user: User = Depends(get_current_user)):
    """
    Get a quick performance summary for dashboard display.
    """
    try:
        # Get recent metrics (last hour)
        cutoff_time = datetime.now(timezone.utc).replace(minute=datetime.now().minute - 60)
        
        recent_metrics = []
        for metric in performance_metrics:
            metric_time = datetime.fromisoformat(metric['timestamp'].replace('Z', '+00:00'))
            if metric_time >= cutoff_time:
                recent_metrics.append(metric)
        
        # Calculate summary stats
        total_recent = len(recent_metrics)
        issues_count = 0
        
        # Count performance issues
        for metric in recent_metrics:
            if metric.get('duration_ms'):
                if metric['metric_type'] == 'token_refresh' and metric['duration_ms'] > 500:
                    issues_count += 1
                elif metric['metric_type'] == 'api_call' and metric['duration_ms'] > 2000:
                    issues_count += 1
        
        return {
            "success": True,
            "summary": {
                "recent_metrics": total_recent,
                "performance_issues": issues_count,
                "status": "good" if issues_count == 0 else "warning" if issues_count < 5 else "critical",
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance summary")

@router.delete("/performance")
async def clear_performance_metrics(current_user: User = Depends(get_current_user)):
    """
    Clear all performance metrics (admin only).
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        global performance_metrics, performance_stats
        metrics_count = len(performance_metrics)
        
        performance_metrics.clear()
        performance_stats.clear()
        
        logger.info(f"Performance metrics cleared by admin {current_user.username}")
        
        return {
            "success": True,
            "message": f"Cleared {metrics_count} performance metrics",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear performance metrics") 