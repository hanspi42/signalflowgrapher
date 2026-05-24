import logging
logger = logging.getLogger(__name__)


def write_file(path, content):
    """
    Write content with utf-8 encoding to file at path.
    """
    try:
        with open(path, "w", encoding='utf8') as f:
            f.write(content)
    except IOError as e:
        logger.error("IO error while writing to file %s: %s",
                     path,
                     str(e))
        raise
    except Exception as e:
        logger.fatal("Unexpected error while writing to file %s: %s",
                     path,
                     str(e))
        raise


def read_file(path) -> str:
    """
    Read content with utf-8 encoding from file at path.
    """
    try:
        with open(path, "r", encoding='utf8') as f:
            return f.read()
    except IOError as e:
        logger.error("IO error while reading from file %s: %s",
                     path,
                     str(e))
        raise
    except Exception as e:
        logger.fatal("Unexpected error while reading from file %s: %s",
                     path,
                     str(e))
        raise
