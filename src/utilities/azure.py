from typing import Any

import azure
from azure.storage.blob import BlobServiceClient, ContentSettings


def azure_download_blob(az_blob_service: BlobServiceClient, container_name: str, blob_name: str, filename: str):

    blob_client = az_blob_service.get_blob_client(container_name, blob_name)

    with open(file=filename, mode="wb") as xml_output:
        download_stream = blob_client.download_blob()
        xml_output.write(download_stream.readall())

    blob_client.close()


def azure_upload_to_blob(
    az_blob_service: BlobServiceClient, container_name: str, blob_name: str, content: Any, content_type: str
):

    blob_client = az_blob_service.get_blob_client(container_name, blob_name)

    content_settings = ContentSettings(content_type=content_type)

    if content_type == "application/xml":
        content_settings.content_encoding = "UTF-8"

    blob_client.upload_blob(content, overwrite=True, content_settings=content_settings)


def create_azure_blob_containers(context: dict):
    blob_service = BlobServiceClient.from_connection_string(context["AZURE_STORAGE_CONNECTION_STRING"])

    containers = blob_service.list_containers()
    container_names = [c.name for c in containers]

    try:
        if context["AZURE_STORAGE_BLOB_CONTAINER_NAME_IATI_XML"] not in container_names:
            blob_service.create_container(context["AZURE_STORAGE_BLOB_CONTAINER_NAME_IATI_XML"])
            container_names.append(context["AZURE_STORAGE_BLOB_CONTAINER_NAME_IATI_XML"])
        if context["AZURE_STORAGE_BLOB_CONTAINER_NAME_IATI_ZIP"] not in container_names:
            blob_service.create_container(context["AZURE_STORAGE_BLOB_CONTAINER_NAME_IATI_ZIP"])
    except Exception as e:
        context["logger"].info("Could not create Azure blob storage containers: {}".format(e))
        raise e
    finally:
        blob_service.close()


def delete_azure_blob_containers(context: dict):
    blob_service = BlobServiceClient.from_connection_string(context["AZURE_STORAGE_CONNECTION_STRING"])

    containers = blob_service.list_containers()
    container_names = [c.name for c in containers]

    try:
        if context["AZURE_STORAGE_BLOB_CONTAINER_NAME_IATI_XML"] in container_names:
            blob_service.delete_container(context["AZURE_STORAGE_BLOB_CONTAINER_NAME_IATI_XML"])
        if context["AZURE_STORAGE_BLOB_CONTAINER_NAME_IATI_ZIP"] in container_names:
            blob_service.delete_container(context["AZURE_STORAGE_BLOB_CONTAINER_NAME_IATI_ZIP"])
    except Exception as e:
        context["logger"].info("Could not delete Azure blob storage container: {}".format(e))
        raise e
    finally:
        blob_service.close()


def delete_azure_iati_blob(context: dict, blob_service_client: BlobServiceClient, dataset: dict, iati_blob_type: str):

    container_name = get_azure_container_name(context, iati_blob_type)

    blob_name = get_azure_blob_name(dataset, iati_blob_type)

    try:
        blob_client = blob_service_client.get_blob_client(container_name, blob_name)

        blob_client.delete_blob()
    except azure.core.exceptions.ResourceNotFoundError as e:
        context["logger"].warning(
            "dataset id: {} - Problem deleting blob that was "
            "expected to exist: {}".format(dataset["id"], e).replace("\n", "")
        )
    finally:
        blob_client.close()


def get_azure_container_name(context: dict, iati_blob_type: str) -> str:
    return context["AZURE_STORAGE_BLOB_CONTAINER_NAME_IATI_" + iati_blob_type.upper()]


def get_azure_blob_name(dataset: dict, iati_blob_type: str) -> str:
    return "{}/{}.{}".format(dataset["publisher_name"], dataset["name"], iati_blob_type)


def get_azure_blob_public_url(context: dict, dataset: dict, iati_blob_type: str) -> str:
    blob_name = get_azure_container_name(context, iati_blob_type)
    blob_name_for_url = "{}/".format(blob_name) if blob_name != "$web" else ""

    return "{}/{}{}".format(
        context["WEB_BASE_URL"],
        blob_name_for_url,
        get_azure_blob_name(dataset, iati_blob_type),
    )
