"""Prometheus metrics middleware"""

import time
import logging
from fastapi import Request, Response

logger = logging.getLogger(__name__)

# Request counters (in production use prometheus_client)
request_counts = {}
request_latencies = {}


async def metrics_middleware(request: Request, call_next):
    """Track request metrics for Prometheus"""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    endpoint = request.url.path
    method = request.method
    status = response.status_code
    
    key = f"{method}:{endpoint}:{status}"
    request_counts[key] = request_counts.get(key, 0) + 1
    
    if endpoint not in request_latencies:
        request_latencies[endpoint] = []
    request_latencies[endpoint].append(duration)
    
    # Add timing header
    response.headers["X-Process-Time"] = str(round(duration * 1000, 2))
    
    return response
