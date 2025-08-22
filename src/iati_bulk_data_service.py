import argparse

from bulk_data_service.checker import checker
from bulk_data_service.registry_changes_processor import registry_changes_processor_start
from bulk_data_service.zipper import zipper
from config.bds_context import BDSContext
from config.config import get_basic_config
from config.initialisation import misc_global_initialisation
from utilities.azure import create_azure_blob_containers
from utilities.db import apply_db_migrations
from utilities.logging import initialise_logging
from utilities.prometheus import initialise_prometheus_client


def main(args: argparse.Namespace):

    config = get_basic_config()

    config = config | {"single_run": args.single_run, "run_for_n_datasets": args.run_for_n_datasets}

    context = BDSContext(config, initialise_logging(config))

    context.logger.info("Bulk Data Service {} initialising...".format(context["BULK_DATA_SERVICE_VERSION"]))

    apply_db_migrations(context)

    create_azure_blob_containers(context)

    misc_global_initialisation(context)

    initialise_prometheus_client(context)

    context.logger.info("Bulk Data Service {} initialisation complete".format(context["BULK_DATA_SERVICE_VERSION"]))

    if args.operation == "checker":
        checker(context)
    elif args.operation == "zipper":
        zipper(context)
    elif args.operation == "registry-changes-processor":
        registry_changes_processor_start(context)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Refresh from IATI Registry")
    parser.add_argument(
        "--operation",
        choices=["checker", "zipper", "registry-changes-processor"],
        required=True,
        help="Operation to run: checker, downloader, registry-changes-processor",
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
