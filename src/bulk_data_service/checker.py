import time
import traceback
import uuid
from datetime import UTC, datetime, timedelta

from bulk_data_service.dataset_indexing import create_and_upload_indices
from bulk_data_service.dataset_remover import remove_deleted_datasets_from_bds, remove_expired_downloads
from bulk_data_service.dataset_updater import add_or_update_datasets
from bulk_data_service.exceptions import SafetyCheckError
from bulk_data_service.reporting_org_sync import add_or_update_reporting_orgs, remove_deleted_reporting_orgs_from_bds
from bulk_data_service.zipper import zipper_run
from config.bds_context import BDSContext
from dataset_registration.registration_proxy import fetch_datasets_metadata, fetch_reporting_orgs_metadata
from utilities.db import get_datasets_in_bds, get_reporting_orgs_in_bds
from utilities.misc import get_timestamp
from utilities.prometheus import get_prom_metric, update_metrics_from_db, update_prom_metric


def checker(context: BDSContext):
    if context["single_run"]:
        checker_run(context, get_datasets_in_bds(context))
    else:
        checker_service_loop(context)


def checker_service_loop(context: BDSContext):

    datasets_in_zip = {}  # type: dict[uuid.UUID, dict]
    datasets_in_bds = get_datasets_in_bds(context)

    while True:
        try:
            checker_run(context, datasets_in_bds)

            zipper_run(context, datasets_in_zip, datasets_in_bds, get_reporting_orgs_in_bds(context))

            context.logger.info("Pausing for {} mins".format(context["CHECKER_LOOP_WAIT_MINS"]))
            time.sleep(60 * int(context["CHECKER_LOOP_WAIT_MINS"]))

        except SafetyCheckError as e:
            context.logger.error("{}. Waiting 10 minutes then re-trying.".format(e))

            time.sleep(60 * 10)

        except Exception as e:
            context.logger.error(
                "Exception in checker service loop. "
                "Waiting 10 minutes then restarting. "
                "Exception message: {}".format(e).replace("\n", "")
            )
            context.logger.error("Full traceback: " "{}".format(traceback.format_exc()))

            get_prom_metric(context, "number_crashes").inc()

            time.sleep(60 * 10)


def checker_run(context: BDSContext, datasets_in_bds: dict[uuid.UUID, dict]):
    run_start = get_timestamp()

    context.logger.info("Checker starting run")

    registered_reporting_orgs = fetch_reporting_orgs_metadata(context, run_start)

    reporting_orgs_in_bds = get_reporting_orgs_in_bds(context)

    perform_safety_check(context, reporting_orgs_in_bds, registered_reporting_orgs, "reporting orgs")

    remove_deleted_reporting_orgs_from_bds(context, reporting_orgs_in_bds, registered_reporting_orgs)

    add_or_update_reporting_orgs(context, registered_reporting_orgs)

    registered_datasets = fetch_datasets_metadata(context, registered_reporting_orgs, get_timestamp())

    perform_safety_check(context, datasets_in_bds, registered_datasets, "datasets")

    remove_deleted_datasets_from_bds(context, datasets_in_bds, registered_datasets)

    add_or_update_datasets(context, datasets_in_bds, registered_datasets)

    remove_expired_downloads(context, datasets_in_bds)

    create_and_upload_indices(context, datasets_in_bds, get_reporting_orgs_in_bds(context))

    update_metrics_from_db(context)

    run_end = datetime.now(UTC)

    update_prom_metric(context, "checker_run_duration", (run_end - run_start).seconds)

    log_checker_stats(context, run_start, run_end, len(registered_datasets))


def perform_safety_check(
    context: BDSContext, existing_items: dict[uuid.UUID, dict], fetched_items: dict[uuid.UUID, dict], item_type: str
):
    if not context.SKIP_SAFETY and len(fetched_items) < len(existing_items) // 2:
        raise SafetyCheckError(
            f"Safety check for {item_type} failed: num fetched ({len(fetched_items)}) is "
            f"less than half the number of existing items ({len(existing_items)})"
        )


def log_checker_stats(context: BDSContext, run_start: datetime, run_end: datetime, num_datasets: int):
    duration = run_end - run_start
    duration_per = duration / num_datasets if num_datasets > 0 else timedelta(0)
    context.logger.info(
        "Checker finished in {}. Datasets processed: {}. Seconds per dataset: {}".format(
            duration,
            num_datasets,
            duration_per.total_seconds(),
        )
    )
