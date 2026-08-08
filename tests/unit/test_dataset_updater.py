from unittest import mock

from bulk_data_service.dataset_updater import add_or_update_dataset_batch


@mock.patch("bulk_data_service.dataset_updater.get_requests_session")
@mock.patch("bulk_data_service.dataset_updater.get_db_connection")
@mock.patch("bulk_data_service.dataset_updater.BlobServiceClient.from_connection_string")
def test_blob_service_client_uses_explicit_default_retries(from_connection_string, get_db_connection, get_session):
    context = {"AZURE_STORAGE_CONNECTION_STRING": "UseDevelopmentStorage=true"}

    add_or_update_dataset_batch(context, {}, {})

    from_connection_string.assert_called_once_with(
        "UseDevelopmentStorage=true",
        retry_total=3,
        retry_connect=3,
        retry_read=3,
        retry_status=3,
        retry_to_secondary=False,
    )
    from_connection_string.return_value.close.assert_called_once_with()
    get_db_connection.return_value.close.assert_called_once_with()
    get_session.return_value.close.assert_called_once_with()
