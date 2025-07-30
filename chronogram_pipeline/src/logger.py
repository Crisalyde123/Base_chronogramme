import json
import logging
import os
from datetime import datetime
from pathlib import Path


def _build_formatter():
    """Return a JSON formatter for log records."""
    try:
        from pythonjsonlogger import jsonlogger

        class CustomJsonFormatter(jsonlogger.JsonFormatter):
            def add_fields(self, log_record, record, message_dict):
                super().add_fields(log_record, record, message_dict)
                # Rename default fields
                log_record['timestamp'] = log_record.pop('asctime')
                log_record['level'] = log_record.pop('levelname')
                log_record['module'] = record.module
                log_record['message'] = record.getMessage()
                # Remove redundant fields
                for key in ['name', 'funcName']:  # keep module only
                    log_record.pop(key, None)

        fmt = '%(asctime)s %(levelname)s %(module)s %(message)s'
        return CustomJsonFormatter(fmt=fmt, datefmt='%Y-%m-%dT%H:%M:%S')
    except Exception:

        class SimpleJsonFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                data = {
                    'timestamp': datetime.utcfromtimestamp(record.created).strftime('%Y-%m-%dT%H:%M:%S'),
                    'level': record.levelname,
                    'module': record.module,
                    'message': record.getMessage(),
                }
                return json.dumps(data)

        return SimpleJsonFormatter()


def get_logger(name: str = "chronologger") -> logging.Logger:
    """Return a configured logger writing JSON logs to console and file."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    base_dir = Path(__file__).resolve().parents[1]
    log_dir = Path(os.getenv("CHRONO_LOG_DIR", base_dir / "data/control"))
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"run_{timestamp}.log"

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)

    formatter = _build_formatter()
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger
