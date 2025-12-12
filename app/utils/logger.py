import logging


def setup_logging(level=logging.INFO):
    root = logging.getLogger()
    if not root.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        handler.setFormatter(formatter)
        root.addHandler(handler)
    root.setLevel(level)
