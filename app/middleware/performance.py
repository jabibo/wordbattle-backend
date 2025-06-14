"""
Performance monitoring middleware for tracking request metrics.
Lightweight implementation that doesn't change core infrastructure.
"""
import time
import logging
from collections import defaultdict
from typing import Dict, List
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Simple performance metrics collector."""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.endpoint_times: Dict[str, List[float]] = defaultdict(list)
        self.request_counts: Dict[str, int] = defaultdict(int)
        self.slow_requests: List[Dict] = []
        
    def record_request(self, method: str, path: str, duration: float):
        """Record request metrics."""
        self.response_times.append(duration)
        endpoint = f"{method} {path}"
        self.endpoint_times[endpoint].append(duration)
        self.request_counts[endpoint] += 1
        
        # Track slow requests (>2 seconds)
        if duration > 2.0:
            self.slow_requests.append({
                "endpoint": endpoint,
                "duration": duration,
                "timestamp": time.time()
            })
            # Keep only last 50 slow requests
            if len(self.slow_requests) > 50:
                self.slow_requests = self.slow_requests[-50:]
    
    def get_stats(self) -> Dict:
        """Get performance statistics."""
        if not self.response_times:
            return {"message": "No requests recorded yet"}
            
        total_requests = len(self.response_times)
        avg_response = sum(self.response_times) / total_requests
        
        # Calculate percentiles
        sorted_times = sorted(self.response_times)
        p50 = sorted_times[int(0.5 * len(sorted_times))]
        p95 = sorted_times[int(0.95 * len(sorted_times))]
        p99 = sorted_times[int(0.99 * len(sorted_times))]
        
        # Top slowest endpoints
        slowest_endpoints = []
        for endpoint, times in self.endpoint_times.items():
            if times:
                avg_time = sum(times) / len(times)
                slowest_endpoints.append({
                    "endpoint": endpoint,
                    "avg_time": round(avg_time, 3),
                    "count": len(times)
                })
        slowest_endpoints.sort(key=lambda x: x["avg_time"], reverse=True)
        
        return {
            "total_requests": total_requests,
            "avg_response_time": round(avg_response, 3),
            "max_response_time": round(max(self.response_times), 3),
            "min_response_time": round(min(self.response_times), 3),
            "percentiles": {
                "p50": round(p50, 3),
                "p95": round(p95, 3),
                "p99": round(p99, 3)
            },
            "slowest_endpoints": slowest_endpoints[:10],
            "slow_requests_count": len(self.slow_requests),
            "recent_slow_requests": self.slow_requests[-5:] if self.slow_requests else []
        }

# Global performance monitor
monitor = PerformanceMonitor()

class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware to track request performance."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        
        # Record metrics
        monitor.record_request(
            method=request.method,
            path=request.url.path,
            duration=duration
        )
        
        # Add performance headers
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        response.headers["X-Request-ID"] = str(hash(f"{start_time}{request.url}"))
        
        # Log slow requests
        if duration > 1.0:
            logger.warning(f"Slow request: {request.method} {request.url.path} took {duration:.3f}s")
            
        return response 