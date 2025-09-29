from bulk_data_service.data_converters import get_full_dataset_check_result_dto
from utilities.misc import get_current_timestamp_as_str


def create_dataset_check_result_msg_payload(
    dataset_record_previous: dict | None, dataset_record_current: dict
) -> dict:

    return {
        "message_type": "DATASET_CHECK_RESULT",
        "message_date": get_current_timestamp_as_str(),
        "dataset_check_result": get_full_dataset_check_result_dto(dataset_record_current),
        "dataset_check_result_previous": (
            get_full_dataset_check_result_dto(dataset_record_previous) if dataset_record_previous is not None else None
        ),
    }
