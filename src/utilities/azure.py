import json
from typing import Any

import azure
import azure.core.exceptions
import azure.servicebus.exceptions
from azure.servicebus import ServiceBusMessage
from azure.storage.blob import BlobServiceClient, ContentSettings

from config.bds_context import BDSContext
from utilities.misc import UUIDDatetimeJSONEncoder


def azure_blob_exists(az_blob_service: BlobServiceClient, container_name: str, blob_name: str) -> bool:
    exists = False
    with az_blob_service.get_blob_client(container_name, blob_name) as blob_client:
        exists = blob_client.exists()
    return exists


def azure_download_blob(az_blob_service: BlobServiceClient, container_name: str, blob_name: str, filename: str):

    blob_client = az_blob_service.get_blob_client(container_name, blob_name)

    with open(file=filename, mode="wb") as xml_output:
        download_stream = blob_client.download_blob()
        xml_output.write(download_stream.readall())

    blob_client.close()


def azure_get_blob_etag(
    context: BDSContext,
    az_blob_service: BlobServiceClient,
    blob_name: str,
) -> str:
    etag = ""

    with az_blob_service.get_blob_client(context["AZURE_STORAGE_BLOB_CONTAINER_NAME"], blob_name) as blob_client:
        if blob_client.exists():
            etag = blob_client.get_blob_properties().etag

    return etag


def azure_upload_to_blob_and_verify(
    context: BDSContext,
    bds_dataset: dict,
    az_blob_service: BlobServiceClient,
    container_name: str,
    blob_name: str,
    content: Any,
    content_type: str,
    encoding: None | str = None,
):

    url = None
    etag = None

    response = azure_upload_to_blob(
        az_blob_service,
        container_name,
        blob_name,
        content,
        content_type,
        encoding=encoding,
    )

    if azure_blob_exists(az_blob_service, container_name, blob_name):
        url = get_azure_blob_public_url(context, bds_dataset, "xml" if content_type == "application/xml" else "zip")
        etag = response["etag"]
    else:
        context.logger.error("dataset id: {} - Azure XML upload failed".format(bds_dataset["id"]))
        context.logger.debug("dataset id: {} - Azure response: {}".format(bds_dataset["id"], response))

    return (url, etag)


def azure_upload_to_blob(
    az_blob_service: BlobServiceClient,
    container_name: str,
    blob_name: str,
    content: Any,
    content_type: str,
    encoding: None | str = None,
) -> dict[str, Any]:

    blob_client = az_blob_service.get_blob_client(container_name, blob_name)

    content_settings = ContentSettings(content_type=content_type)

    if content_type == "application/xml":
        content_settings.content_encoding = encoding

    return blob_client.upload_blob(content, overwrite=True, content_settings=content_settings)


def create_azure_blob_containers(context: BDSContext):
    blob_service = BlobServiceClient.from_connection_string(context["AZURE_STORAGE_CONNECTION_STRING"])

    containers = blob_service.list_containers()
    container_names = [c.name for c in containers]

    try:
        if context["AZURE_STORAGE_BLOB_CONTAINER_NAME"] not in container_names:
            blob_service.create_container(context["AZURE_STORAGE_BLOB_CONTAINER_NAME"])
            container_names.append(context["AZURE_STORAGE_BLOB_CONTAINER_NAME"])
    except Exception as e:
        context.logger.error(
            "Could not create Azure blob storage container. "
            "Container name: {}. "
            "Error details: {}".format(
                context["AZURE_STORAGE_BLOB_CONTAINER_NAME"],
                e,
            )
        )
        raise e
    finally:
        blob_service.close()


def delete_azure_blob_containers(context: BDSContext):
    blob_service = BlobServiceClient.from_connection_string(context["AZURE_STORAGE_CONNECTION_STRING"])

    containers = blob_service.list_containers()
    container_names = [c.name for c in containers]

    try:
        if context["AZURE_STORAGE_BLOB_CONTAINER_NAME"] in container_names:
            blob_service.delete_container(context["AZURE_STORAGE_BLOB_CONTAINER_NAME"])
            container_names.remove(context["AZURE_STORAGE_BLOB_CONTAINER_NAME"])
    except Exception as e:
        context.logger.error("Could not delete Azure blob storage container: {}".format(e))
        raise e
    finally:
        blob_service.close()


def delete_azure_iati_blob(
    context: BDSContext, blob_service_client: BlobServiceClient, dataset: dict, iati_blob_type: str
):

    container_name = get_azure_container_name(context, iati_blob_type)

    blob_name = get_azure_blob_name(dataset, iati_blob_type)

    try:
        blob_client = blob_service_client.get_blob_client(container_name, blob_name)

        blob_client.delete_blob()
    except azure.core.exceptions.ResourceNotFoundError as e:
        context.logger.error(
            "dataset id: {} - Problem deleting blob that was "
            "expected to exist: {}".format(dataset["id"], e).replace("\n", "")
        )
    finally:
        blob_client.close()


def get_azure_container_name(context: BDSContext, iati_blob_type: str) -> str:
    return context["AZURE_STORAGE_BLOB_CONTAINER_NAME"]


def get_azure_blob_name(dataset: dict, iati_blob_type: str) -> str:
    return "{}/{}.{}".format(dataset["reporting_org_short_name"], dataset["short_name"], iati_blob_type)


def get_azure_blob_public_url(context: BDSContext, dataset: dict, iati_blob_type: str) -> str:
    blob_name = get_azure_container_name(context, iati_blob_type)
    blob_name_for_url = "{}/".format(blob_name) if blob_name != "$web" else ""

    return "{}/{}{}".format(
        context["WEB_BASE_URL"],
        blob_name_for_url,
        get_azure_blob_name(dataset, iati_blob_type),
    )


def send_dataset_check_result_message(context: BDSContext, msg_payload: dict, retries: int = 1):

    topic_name = context["AZURE_SERVICE_BUS_DATASET_CHECK_RESULTS_TOPIC_NAME"]

    for retry_number in range(1, retries + 1):
        try:
            send_message_to_iati_mq(context, topic_name, msg_payload)
            break
        except azure.servicebus.exceptions.ServiceBusConnectionError as e:
            if retry_number == retries:
                raise RuntimeError("{}".format(e))


def send_message_to_iati_mq(context: BDSContext, topic_name, msg_payload):

    conn_str = context["AZURE_SERVICE_BUS_CONNECTION_STRING"]

    payload = json.dumps(msg_payload, cls=UUIDDatetimeJSONEncoder, indent=2)

    servicebus_client = context.service_factory.get_service_bus_client(conn_str)

    sender = servicebus_client.get_topic_sender(topic_name)

    message = ServiceBusMessage(body=payload, application_properties={"message_type": msg_payload["message_type"]})

    sender.send_messages(message)

    sender.close()

    servicebus_client.close()


def upload_zip_to_azure(context: BDSContext, zip_local_pathname: str, zip_azure_filename: str):
    az_blob_service = BlobServiceClient.from_connection_string(context["AZURE_STORAGE_CONNECTION_STRING"])

    blob_client = az_blob_service.get_blob_client(context["AZURE_STORAGE_BLOB_CONTAINER_NAME"], zip_azure_filename)

    content_settings = ContentSettings(content_type="zip")

    with open(zip_local_pathname, "rb") as data:
        blob_client.upload_blob(data, overwrite=True, content_settings=content_settings)

    az_blob_service.close()
