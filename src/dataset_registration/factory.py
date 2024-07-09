import uuid
from typing import Callable


def get_func_to_fetch_list_registered_datasets(config: dict) -> Callable[..., dict[uuid.UUID, dict]]:
    if config["DATA_REGISTRATION"] == "ckan-registry":
        from dataset_registration.iati_registry_ckan import fetch_datasets_metadata
    else:
        from dataset_registration.iati_register_your_data import fetch_datasets_metadata
    return fetch_datasets_metadata
