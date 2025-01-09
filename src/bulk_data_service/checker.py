import datetime
import time
import traceback
import uuid

from bulk_data_service.dataset_indexing import create_and_upload_indices
from bulk_data_service.dataset_remover import remove_deleted_datasets_from_bds, remove_expired_downloads
from bulk_data_service.dataset_updater import add_or_update_datasets
from bulk_data_service.reporting_org_sync import add_or_update_reporting_orgs, remove_deleted_reporting_orgs_from_bds
from bulk_data_service.zipper import zipper_run
from dataset_registration.iati_registry_ckan import fetch_datasets_metadata, fetch_reporting_orgs_metadata
from utilities.db import get_datasets_in_bds, get_reporting_orgs_in_bds
from utilities.prometheus import initialise_prometheus_client, update_metrics_from_db


def checker(context: dict):
    context = initialise_prometheus_client(context)

    if context["single_run"]:
        checker_run(context, get_datasets_in_bds(context))
    else:
        checker_service_loop(context)


def checker_service_loop(context: dict):

    datasets_in_zip = {}  # type: dict[uuid.UUID, dict]
    datasets_in_bds = get_datasets_in_bds(context)

    while True:
        try:
            checker_run(context, datasets_in_bds)

            zipper_run(context, datasets_in_zip, datasets_in_bds)

            context["logger"].info("Pausing for {} mins".format(context["CHECKER_LOOP_WAIT_MINS"]))
            time.sleep(60 * int(context["CHECKER_LOOP_WAIT_MINS"]))

        except Exception as e:
            context["logger"].error(
                "Exception in checker service loop. "
                "Waiting 10 minutes then restarting. "
                "Exception message: {}".format(e).replace("\n", "")
            )
            context["logger"].error("Full traceback: " "{}".format(traceback.format_exc()))

            context["prom_metrics"]["number_crashes"].inc()

            time.sleep(60 * 10)


def checker_run(context: dict, datasets_in_bds: dict[uuid.UUID, dict]):
    run_start = datetime.datetime.now(datetime.UTC)

    context["logger"].info("Checker starting run")

    registered_reporting_orgs = fetch_reporting_orgs_metadata(context)

    reporting_orgs_in_bds = get_reporting_orgs_in_bds(context)

    remove_deleted_reporting_orgs_from_bds(context, reporting_orgs_in_bds, registered_reporting_orgs)

    add_or_update_reporting_orgs(context, registered_reporting_orgs)

    registered_datasets = fetch_datasets_metadata(context, registered_reporting_orgs)

    remove_deleted_datasets_from_bds(context, datasets_in_bds, registered_datasets)

    add_or_update_datasets(context, datasets_in_bds, registered_datasets)

    remove_expired_downloads(context, datasets_in_bds)

    create_and_upload_indices(context, datasets_in_bds, registered_reporting_orgs)

    update_metrics_from_db(context)

    run_end = datetime.datetime.now(datetime.UTC)

    context["prom_metrics"]["checker_run_duration"].set((run_end - run_start).seconds)

    context["logger"].info(
        "Checker finished in {}. Datasets processed: {}. Seconds per dataset: {}".format(
            run_end - run_start,
            len(registered_datasets),
            ((run_end - run_start) / len(registered_datasets)).total_seconds(),
        )
    )
