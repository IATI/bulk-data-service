import uuid

import requests

from dataset_registration.factory import get_func_to_fetch_list_registered_datasets


def get_registered_datasets(context: dict) -> dict[uuid.UUID, dict]:
    session = requests.Session()

    fetch_datasets_metadata = get_func_to_fetch_list_registered_datasets(context)

    datasets_metadata = fetch_datasets_metadata(context, session)

    return datasets_metadata
