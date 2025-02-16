import logging
from argparse import Namespace


def sqa_logging(args: Namespace) -> None:
    if args.verbose:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    else:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
