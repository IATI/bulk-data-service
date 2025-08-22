import uuid

import requests

from config.bds_context import BDSContext


def fetch_datasets_metadata(context: BDSContext, session: requests.Session) -> dict[uuid.UUID, dict]:
    return {}


def fetch_reporting_orgs_metadata(context: BDSContext, session: requests.Session) -> dict[uuid.UUID, dict]:
    return {}
