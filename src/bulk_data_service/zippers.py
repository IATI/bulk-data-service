import json
import os
import shutil
import uuid
from abc import ABC, abstractmethod

from azure.storage.blob import BlobServiceClient

from bulk_data_service.dataset_indexing import get_dataset_index_name, get_reporting_org_index_name
from utilities.azure import azure_download_blob, get_azure_container_name, upload_zip_to_azure
from utilities.misc import (
    dataset_has_iati_xml_download,
    filter_dict_by_structure,
    get_number_xml_files_in_dir,
    get_timestamp_as_str_z,
    lookup_license_title_from_id,
)


class IATIDataZipper(ABC):

    def __init__(
        self,
        context,
        zip_working_dir: str,
        datasets_in_working_dir: dict[uuid.UUID, dict],
        datasets_in_bds: dict[uuid.UUID, dict],
        reporting_orgs: dict[uuid.UUID, dict],
    ):
        self.context = context
        self.datasets_in_working_dir = datasets_in_working_dir
        self.datasets_in_bds = datasets_in_bds
        self.reporting_orgs = reporting_orgs
        self.zip_working_dir = zip_working_dir

    @abstractmethod
    def prepare(self):
        pass

    @property
    @abstractmethod
    def zip_type(self) -> str:
        pass

    @property
    def zip_internal_directory_name(self) -> str:
        return "iati-data"

    @property
    def zip_local_filename_no_extension(self) -> str:
        return "iati-data"

    def zip(self):
        self.context["logger"].info("Zipping {} datasets.".format(get_number_xml_files_in_dir(self.zip_working_dir)))
        shutil.make_archive(
            self.get_zip_local_pathname_no_extension(),
            "zip",
            root_dir=self.zip_working_dir,
            base_dir=self.zip_internal_directory_name,
        )

    def upload(self):
        self.context["logger"].info(
            "Uploading {} ZIP to Azure with filename: {}.".format(self.zip_type, self.get_zip_local_filename())
        )
        upload_zip_to_azure(self.context, self.get_zip_local_pathname(), self.get_zip_local_filename())

    def get_zip_local_filename(self) -> str:
        return "{}.zip".format(self.zip_local_filename_no_extension)

    def get_zip_local_pathname(self) -> str:
        return "{}/{}".format(self.zip_working_dir, self.get_zip_local_filename())

    def get_zip_local_pathname_no_extension(self) -> str:
        return "{}/{}".format(self.zip_working_dir, self.zip_local_filename_no_extension)


class IATIBulkDataServiceZipper(IATIDataZipper):

    def prepare(self):
        az_blob_service = BlobServiceClient.from_connection_string(self.context["AZURE_STORAGE_CONNECTION_STRING"])

        self.download_dataset_index_to_working_dir(az_blob_service, "minimal")

        self.download_dataset_index_to_working_dir(az_blob_service, "full")

        self.download_reporting_org_index_to_working_dir(az_blob_service)

        az_blob_service.close()

    @property
    def zip_type(self) -> str:
        return "Bulk Data Service"

    def download_dataset_index_to_working_dir(self, az_blob_service: BlobServiceClient, index_type: str):

        index_filename = get_dataset_index_name(self.context, index_type)

        index_pathname = "{}/{}/{}".format(
            self.zip_working_dir, self.zip_internal_directory_name, "{}.json".format(index_filename)
        )

        os.makedirs(os.path.dirname(index_pathname), exist_ok=True)

        azure_download_blob(
            az_blob_service, get_azure_container_name(self.context, "xml"), index_filename, index_pathname
        )

    def download_reporting_org_index_to_working_dir(self, az_blob_service: BlobServiceClient):

        index_filename = get_reporting_org_index_name(self.context)

        index_pathname = "{}/{}/{}".format(
            self.zip_working_dir, self.zip_internal_directory_name, "{}.json".format(index_filename)
        )

        os.makedirs(os.path.dirname(index_pathname), exist_ok=True)

        azure_download_blob(
            az_blob_service, get_azure_container_name(self.context, "xml"), index_filename, index_pathname
        )


class CodeforIATILegacyZipper(IATIDataZipper):

    def get_dataset_metadata_in_ckan_format(self, dataset: dict) -> str:
        return json.dumps(
            {
                "id": str(dataset["id"]),
                "license_id": dataset["license_id"],
                "license_title": lookup_license_title_from_id(dataset["license_id"]),
                "name": dataset["short_name"],
                "organization": {"id": str(dataset["reporting_org_id"]), "name": dataset["reporting_org_short_name"]},
                "resources": [{"url": dataset["source_url"]}],
                "extras": [],
                "tags": [],
                "groups": [],
                "users": [],
            }
        )

    def get_reporting_org_metadata_in_ckan_format(self, dataset: dict) -> str:
        return json.dumps({"id": str(dataset["reporting_org_id"]), "name": dataset["reporting_org_short_name"]})

    def prepare(self):
        # rename 'iati-data' directory to 'iati-data-main'
        if os.path.exists(os.path.join(self.zip_working_dir, super().zip_internal_directory_name)):
            os.rename(
                os.path.join(self.zip_working_dir, super().zip_internal_directory_name),
                os.path.join(self.zip_working_dir, self.zip_internal_directory_name),
            )

        # rename 'datasets' directory to 'data'
        if os.path.exists(os.path.join(self.zip_working_dir, self.zip_internal_directory_name, "datasets")):
            os.rename(
                os.path.join(self.zip_working_dir, self.zip_internal_directory_name, "datasets"),
                os.path.join(self.zip_working_dir, self.zip_internal_directory_name, "data"),
            )

        self.create_empty_files_for_non_downloadable_datasets()

        if not os.path.exists(os.path.join(self.zip_working_dir, self.zip_internal_directory_name, "metadata")):
            os.makedirs(os.path.join(self.zip_working_dir, self.zip_internal_directory_name, "metadata"))

        self.write_publisher_metadata_files()

        self.write_transformed_dataset_metadata_files()

        # create root 'metadata.json' file with created timestsamp
        self.create_zip_file_metadata()

    def create_empty_files_for_non_downloadable_datasets(self):
        for dataset_in_bds_db in self.datasets_in_bds:
            dataset = self.datasets_in_bds[dataset_in_bds_db]
            dataset_pathname = self.get_dataset_data_pathname(self.datasets_in_bds[dataset_in_bds_db])
            dataset_filename = self.get_dataset_data_filename(self.datasets_in_bds[dataset_in_bds_db])
            if not dataset_has_iati_xml_download(dataset):
                if not os.path.exists(dataset_pathname):
                    os.makedirs(dataset_pathname, exist_ok=True)
            if not os.path.exists(dataset_filename):
                open(dataset_filename, "w").close()

    def write_publisher_metadata_files(self):
        for dataset_in_bds_db in self.datasets_in_bds:
            reporting_org_metadata_filename = self.get_publisher_metadata_filename(
                self.datasets_in_bds[dataset_in_bds_db]["reporting_org_short_name"]
            )
            if not os.path.exists(reporting_org_metadata_filename):
                with open(reporting_org_metadata_filename, "w") as pub_file:
                    reporting_org_metadata = "{}"
                    if self.datasets_in_bds[dataset_in_bds_db]["reporting_org_id"] in self.reporting_orgs:
                        reporting_org_metadata = self.get_reporting_org_metadata_in_ckan_format(
                            self.datasets_in_bds[dataset_in_bds_db]
                        )
                    pub_file.write(reporting_org_metadata)

    def get_publisher_metadata_filename(self, reporting_org_short_name):
        return os.path.join(
            self.zip_working_dir, self.zip_internal_directory_name, "metadata", f"{reporting_org_short_name}.json"
        )

    def write_transformed_dataset_metadata_files(self):
        for dataset_in_bds_db in self.datasets_in_bds:
            dataset_metadata_pathname = self.get_dataset_metadata_pathname(self.datasets_in_bds[dataset_in_bds_db])
            dataset_metadata_filename = self.get_dataset_metadata_filename(self.datasets_in_bds[dataset_in_bds_db])
            if not os.path.exists(dataset_metadata_pathname):
                os.makedirs(dataset_metadata_pathname, exist_ok=True)
            if not os.path.exists(dataset_metadata_filename):
                with open(dataset_metadata_filename, "w") as pub_file:
                    pub_file.write(self.get_dataset_metadata_in_ckan_format(self.datasets_in_bds[dataset_in_bds_db]))

    def get_dataset_data_pathname(self, dataset_in_bds):
        return os.path.join(
            self.zip_working_dir,
            self.zip_internal_directory_name,
            "data",
            f"{dataset_in_bds['reporting_org_short_name']}",
        )

    def get_dataset_data_filename(self, dataset_in_bds):
        return os.path.join(self.get_dataset_data_pathname(dataset_in_bds), f"{dataset_in_bds['short_name']}.xml")

    def get_dataset_metadata_pathname(self, dataset_in_bds):
        return os.path.join(
            self.zip_working_dir,
            self.zip_internal_directory_name,
            "metadata",
            f"{dataset_in_bds['reporting_org_short_name']}",
        )

    def get_dataset_metadata_filename(self, dataset_in_bds):
        return os.path.join(self.get_dataset_metadata_pathname(dataset_in_bds), f"{dataset_in_bds['short_name']}.json")

    @property
    def zip_type(self) -> str:
        return "Code for IATI"

    @property
    def zip_internal_directory_name(self) -> str:
        return "iati-data-main"

    @property
    def zip_local_filename_no_extension(self) -> str:
        return "code-for-iati-data-download"

    def create_zip_file_metadata(self):
        with open(
            "{}/{}/{}".format(self.zip_working_dir, self.zip_internal_directory_name, "metadata.json"), "w"
        ) as metadata_file:
            json.dump({"created_at": get_timestamp_as_str_z(), "updated_at": get_timestamp_as_str_z()}, metadata_file)
