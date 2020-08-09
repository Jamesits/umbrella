import logging
logger = logging.getLogger(__name__)


def init_logging():
    logger.debug("Initializing logging config")
    formatter = logging.Formatter(fmt='%(asctime)s|%(levelname)s|%(module)s: %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
    logger.debug("Initialized logging config")
