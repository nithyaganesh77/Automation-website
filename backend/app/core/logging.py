import logging
import sys
import json
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Structured JSON formatter for production log aggregation."""
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno
        }
        if hasattr(record, "document_id"):
            log_obj["document_id"] = getattr(record, "document_id")
        if hasattr(record, "org_id"):
            log_obj["org_id"] = getattr(record, "org_id")
        if hasattr(record, "agent_name"):
            log_obj["agent_name"] = getattr(record, "agent_name")
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logging():
    logger = logging.getLogger("documind")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    
    return logger


logger = setup_logging()
