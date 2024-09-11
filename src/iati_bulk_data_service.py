import argparse

from bulk_data_service.checker import checker
from bulk_data_service.zipper import zipper
from config.config import get_config
from config.initialisation import misc_global_initialisation
from utilities.azure import create_azure_blob_containers
from utilities.db import apply_db_migrations
from utilities.logging import initialise_logging


def main(args: argparse.Namespace):

    config = get_config()

    logger = initialise_logging(config)

    context = config | {"logger": logger, "single_run": args.single_run, "run_for_n_datasets": args.run_for_n_datasets}

    apply_db_migrations(context)

    create_azure_blob_containers(context)

    misc_global_initialisation(context)

    if args.operation == "checker":
        checker(context)
    elif args.operation == "zipper":
        zipper(context)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Refresh from IATI Registry")
    parser.add_argument(
        "--operation",
        choices=["checker", "zipper"],
        required=True,
        help="Operation to run: checker, downloader",
    )
    parser.add_argument(
        "--single-run",
        action="store_true",
        help="Perform a single run, then exit",
    )
    parser.add_argument(
        "--run-for-n-datasets",
        type=int,
        help="Run on the first N datasets from registration service (useful for testing)",
    )
    main(parser.parse_args())
