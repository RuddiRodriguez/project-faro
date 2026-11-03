import logging

from faro_signal.common_tools.logger_metadata import LoggerMetadata
from utils.logger import setup_logger


logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logger = setup_logger(logger_name=__name__, log_level=logging.INFO)


class PredictorLogger:
    @staticmethod
    def log_error(metadata: LoggerMetadata | None, message: str) -> None:
        details = metadata.model_dump(exclude_none=True) if metadata else {}
        logger.error("Message=%s Metadata=%s", message, details)
