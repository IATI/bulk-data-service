import uuid
from datetime import datetime

from config.bds_context import BDSContext
from dataset_registration import iati_registry_ckan, iati_registry_suitecrm


def fetch_datasets_metadata(
    context: BDSContext, registered_reporting_orgs: dict, refresh_timestamp: datetime
) -> dict[uuid.UUID, dict]:
    registered_datasets = {}

    if context["DATA_REGISTRATION"] == "ckan-registry":
        registered_datasets = iati_registry_ckan.fetch_datasets_metadata(context, registered_reporting_orgs)
    elif context["DATA_REGISTRATION"] == "suitecrm-registry":
        registered_datasets = iati_registry_suitecrm.fetch_datasets_metadata(
            context, registered_reporting_orgs, refresh_timestamp
        )
    else:
        raise ValueError("Misconfiguration: unknown DATA_REGISTRATION value: {}".format(context["DATA_REGISTRATION"]))

    return registered_datasets


def fetch_reporting_orgs_metadata(context: BDSContext, refresh_timestamp: datetime) -> dict[uuid.UUID, dict]:
    registered_reporting_orgs = {}

    if context["DATA_REGISTRATION"] == "ckan-registry":
        registered_reporting_orgs = iati_registry_ckan.fetch_reporting_orgs_metadata(context, refresh_timestamp)
    elif context["DATA_REGISTRATION"] == "suitecrm-registry":
        registered_reporting_orgs = iati_registry_suitecrm.fetch_reporting_orgs_metadata(context, refresh_timestamp)
    else:
        raise ValueError("Misconfiguration: unknown DATA_REGISTRATION value: {}".format(context["DATA_REGISTRATION"]))

    return registered_reporting_orgs
