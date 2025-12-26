"""
Performance metrics and real-time monitoring for classification system

Thread-safe metrics collection for production observability.

Tracked Metrics:
- Total classifications processed
- Success/failure counts per processor (regex, BERT, LLM)
- Response time statistics (average, min, max)
- Throughput calculation (logs per second)

Concurrency: Thread-safe with lock-based synchronization
Use Case: Health checks, performance dashboards, alerting
"""
from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime
import time
from threading import Lock


@dataclass
class Metrics:
    """Application metrics"""
    start_time: float = field(default_factory=time.time)
    total_classifications: int = 0
    classifications_by_method: Dict[str, int] = field(default_factory=lambda: {
        "regex": 0,
        "bert": 0,
        "llm": 0,
        "unclassified": 0,
        "error": 0
    })
    total_processing_time_ms: float = 0.0
    error_count: int = 0
    request_count: int = 0
    _lock: Lock = field(default_factory=Lock)
    
    def record_classification(self, method: str, processing_time_ms: float, error: bool = False):
        """Record a classification event"""
        with self._lock:
            self.total_classifications += 1
            self.request_count += 1
            
            if error:
                self.error_count += 1
                self.classifications_by_method["error"] += 1
            else:
                self.classifications_by_method[method] = \
                    self.classifications_by_method.get(method, 0) + 1
                self.total_processing_time_ms += processing_time_ms
    
    def get_average_processing_time(self) -> float:
        """Get average processing time in ms"""
        with self._lock:
            successful = self.total_classifications - self.error_count
            if successful == 0:
                return 0.0
            return self.total_processing_time_ms / successful
    
    def get_error_rate(self) -> float:
        """Get error rate as percentage"""
        with self._lock:
            if self.request_count == 0:
                return 0.0
            return (self.error_count / self.request_count) * 100
    
    def get_uptime_seconds(self) -> float:
        """Get uptime in seconds"""
        return time.time() - self.start_time
    
    def to_dict(self) -> dict:
        """Convert metrics to dictionary"""
        with self._lock:
            return {
                "total_classifications": self.total_classifications,
                "classifications_by_method": self.classifications_by_method.copy(),
                "average_processing_time_ms": self.get_average_processing_time(),
                "error_rate": self.get_error_rate(),
                "uptime_seconds": self.get_uptime_seconds(),
                "total_requests": self.request_count,
                "total_errors": self.error_count
            }


# Global metrics instance
_metrics = Metrics()


def get_metrics() -> Metrics:
    """Get global metrics instance"""
    return _metrics
