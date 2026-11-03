import logging


# Mute verbose loggers
logging.getLogger('boto3').setLevel(logging.WARNING)
logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)


def setup_logger(logger_name, log_level=logging.DEBUG):
    logger = logging.getLogger(logger_name)
    if logger.hasHandlers():
        logger.setLevel(log_level)
    else:
        logging.basicConfig(level=log_level)

    return logger
