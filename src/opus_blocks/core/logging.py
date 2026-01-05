import logging


def configure_logging(environment: str) -> None:
    log_level = logging.INFO
    if environment.lower() in {"local", "development"}:
        log_level = logging.DEBUG

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
