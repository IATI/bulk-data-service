import json
import os
import zipfile

import requests

from bulk_data_service.checker import checker_run
from bulk_data_service.zipper import zipper_run
from helpers.helpers import get_and_clear_up_context, get_number_xml_files_in_working_dir  # noqa: F401
from utilities.db import get_reporting_orgs_in_bds


def test_dataset_saved_for_download_success(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    run_checker_then_zipper_once(context)

    assert get_number_xml_files_in_working_dir(context) == 1
    assert (
        os.path.exists(
            "{}{}".format(
                context["ZIP_WORKING_DIR"], "/iati-data/datasets/test_foundation_a/test_foundation_a-dataset-001.xml"
            )
        )
        is True
    )


def test_dataset_not_saved_for_download_fail_and_no_cache(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    run_checker_then_zipper_download_fail(context)

    assert get_number_xml_files_in_working_dir(context) == 0


def test_dataset_saved_for_download_fail_but_cached(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    run_checker_then_zipper_download_fail_but_cached(context)

    assert get_number_xml_files_in_working_dir(context) == 1
    assert (
        os.path.exists(
            "{}{}".format(
                context["ZIP_WORKING_DIR"], "/iati-data/datasets/test_foundation_a/test_foundation_a-dataset-001.xml"
            )
        )
        is True
    )


def test_publisher_metadata_saved_for_failed_metadata_dl(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    run_checker_then_zipper_once(context)

    download_and_unpack_zip_to_tmp_unpack_folder(context, "code-for-iati-data-download.zip")

    assert os.path.exists(context["TEST_TMP_ZIP_UNPACK"] + "/iati-data-main/metadata/test_foundation_a.json") is True


def test_publisher_metadata_saved_for_successful_metadata_dl(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-05-1-dataset-updated"
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    datasets_in_zip = {}
    zipper_run(context, datasets_in_zip, datasets_in_bds, get_reporting_orgs_in_bds(context))

    download_and_unpack_zip_to_tmp_unpack_folder(context, "code-for-iati-data-download.zip")

    assert os.path.exists(context["TEST_TMP_ZIP_UNPACK"] + "/iati-data-main/metadata/test_foundation_a.json") is True


def test_publisher_metadata_content_for_successful_metadata_dl(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-05-1-dataset-updated"
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    datasets_in_zip = {}
    zipper_run(context, datasets_in_zip, datasets_in_bds, get_reporting_orgs_in_bds(context))

    download_and_unpack_zip_to_tmp_unpack_folder(context, "code-for-iati-data-download.zip")

    with open(context["TEST_TMP_ZIP_UNPACK"] + "/iati-data-main/metadata/test_foundation_a.json", "r") as f:
        assert f.read() == json.dumps(
            {
                "id": "ea055d99-f7e9-456f-9f99-963e95493c1b",
                "name": "test_foundation_a",
            }
        )


def test_dataset_metadata_content_for_successful_metadata_dl(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-05-1-dataset-updated"
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    datasets_in_zip = {}
    zipper_run(context, datasets_in_zip, datasets_in_bds, get_reporting_orgs_in_bds(context))

    download_and_unpack_zip_to_tmp_unpack_folder(context, "code-for-iati-data-download.zip")

    with open(
        context["TEST_TMP_ZIP_UNPACK"]
        + "/iati-data-main/metadata/test_foundation_a/test_foundation_a-dataset-001-newname.json",
        "r",
    ) as f:
        assert f.read() == json.dumps(
            {
                "id": "c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159",
                "license_id": "uk-ogl",
                "license_title": "UK Open Government Licence (OGL)",
                "name": "test_foundation_a-dataset-001-newname",
                "organization": {
                    "id": "ea055d99-f7e9-456f-9f99-963e95493c1b",
                    "name": "test_foundation_a",
                },
                "resources": [{"url": "http://localhost:3000/not_found"}],
                "extras": [],
                "tags": [],
                "groups": [],
                "users": [],
            }
        )


def test_bds_zip_content_for_download_success(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    run_checker_then_zipper_once(context)

    download_and_unpack_zip_to_tmp_unpack_folder(context)

    assert file_found_in_extracted_zip(context, "iati-data/datasets-minimal.json")
    assert file_found_in_extracted_zip(context, "iati-data/datasets-full.json")
    assert file_found_in_extracted_zip(context, "iati-data/reporting-orgs.json")
    assert file_found_in_extracted_zip(
        context, "iati-data/datasets/test_foundation_a/test_foundation_a-dataset-001.xml"
    )


def test_bds_zip_content_for_download_success_dataset_updated_meta(get_and_clear_up_context, tmp_path):  # noqa: F811
    """Checks that when a dataset's short_name is altered, the dataset is found in the ZIP with new but not old name"""

    context = get_and_clear_up_context

    datasets_in_bds = {}
    datasets_in_zip = {}

    run_checker_then_zipper(
        context, "http://localhost:3000/ckan-registration/datasets-01-1-dataset", datasets_in_bds, datasets_in_zip
    )

    run_checker_then_zipper(
        context,
        "http://localhost:3000/ckan-registration/datasets-06-1-dataset-updated-metadata",
        datasets_in_bds,
        datasets_in_zip,
    )

    download_and_unpack_zip_to_tmp_unpack_folder(context)

    assert file_found_in_extracted_zip(context, "iati-data/datasets-minimal.json")
    assert file_found_in_extracted_zip(context, "iati-data/datasets-full.json")
    assert file_found_in_extracted_zip(context, "iati-data/reporting-orgs.json")
    assert file_found_in_extracted_zip(
        context, "iati-data/datasets/test_foundation_a/test_foundation_a-dataset-001-newname.xml"
    )

    # The dataset as it was originally named should not be found
    assert not file_found_in_extracted_zip(
        context, "iati-data/datasets/test_foundation_a/test_foundation_a-dataset-001.xml"
    )


def test_bds_zip_content_for_download_success_dataset_updated_content(get_and_clear_up_context):  # noqa: F811
    """Checks that when dataset contents (but not metadata) is updated the new file contents is found in the ZIP"""

    context = get_and_clear_up_context

    datasets_in_bds = {}
    datasets_in_zip = {}

    run_checker_then_zipper(
        context, "http://localhost:3000/ckan-registration/datasets-01-1-dataset", datasets_in_bds, datasets_in_zip
    )

    run_checker_then_zipper(
        context,
        (
            "http://localhost:3000/ckan-registration/datasets-01-1-dataset/"
            "http%3A%2F%2Flocalhost%3A3000%2Fdata%2Ftest_foundation_a-dataset-001-updated.xml"
        ),
        datasets_in_bds,
        datasets_in_zip,
    )

    download_and_unpack_zip_to_tmp_unpack_folder(context)

    assert file_found_in_extracted_zip(context, "iati-data/datasets-minimal.json")

    with open(
        os.path.join(
            context["TEST_TMP_ZIP_UNPACK"], "iati-data/datasets/test_foundation_a/test_foundation_a-dataset-001.xml"
        ),
        "rb",
    ) as f:
        contents_from_zip = f.read()

    with open("tests/artifacts/iati-xml-files/test_foundation_a-dataset-001-updated.xml", "rb") as f:
        contents_from_disk = f.read()

    assert contents_from_disk == contents_from_zip


def test_bds_zip_content_for_download_fail_but_cached(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    run_checker_then_zipper_download_fail_but_cached(context)

    download_and_unpack_zip_to_tmp_unpack_folder(context)

    assert file_found_in_extracted_zip(context, "iati-data/datasets-minimal.json")
    assert file_found_in_extracted_zip(context, "iati-data/datasets-full.json")
    assert file_found_in_extracted_zip(context, "iati-data/reporting-orgs.json")
    assert file_found_in_extracted_zip(
        context, "iati-data/datasets/test_foundation_a/test_foundation_a-dataset-001.xml"
    )


def test_bds_zip_content_for_download_fail_no_cached(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    run_checker_then_zipper_download_fail(context)

    download_and_unpack_zip_to_tmp_unpack_folder(context)

    assert file_found_in_extracted_zip(context, "iati-data/datasets-minimal.json")
    assert file_found_in_extracted_zip(context, "iati-data/datasets-full.json")
    assert file_found_in_extracted_zip(context, "iati-data/reporting-orgs.json")
    assert not file_found_in_extracted_zip(
        context, "iati-data/datasets/test_foundation_a/test_foundation_a-dataset-001.xml"
    )


def test_codeforiati_zip_content_for_download_success(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    run_checker_then_zipper_once(context)

    download_and_unpack_zip_to_tmp_unpack_folder(context, "code-for-iati-data-download.zip")

    assert not file_found_in_extracted_zip(context, "iati-data/datasets-minimal.json")
    assert not file_found_in_extracted_zip(context, "iati-data/datasets-full.json")
    assert not file_found_in_extracted_zip(context, "iati-data/reporting-orgs.json")
    assert file_found_in_extracted_zip(context, "iati-data-main/metadata.json")
    assert file_found_in_extracted_zip(
        context, "iati-data-main/data/test_foundation_a/test_foundation_a-dataset-001.xml"
    )
    assert file_found_in_extracted_zip(context, "iati-data-main/metadata/test_foundation_a.json")
    assert file_found_in_extracted_zip(
        context, "iati-data-main/metadata/test_foundation_a/test_foundation_a-dataset-001.json"
    )


def test_codeforiati_zip_content_for_download_fail_but_cached(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    run_checker_then_zipper_download_fail_but_cached(context)

    download_and_unpack_zip_to_tmp_unpack_folder(context, "code-for-iati-data-download.zip")

    assert not file_found_in_extracted_zip(context, "iati-data/datasets-minimal.json")
    assert not file_found_in_extracted_zip(context, "iati-data/datasets-full.json")
    assert not file_found_in_extracted_zip(context, "iati-data/reporting-orgs.json")
    assert file_found_in_extracted_zip(context, "iati-data-main/metadata.json")
    assert file_found_in_extracted_zip(
        context, "iati-data-main/data/test_foundation_a/test_foundation_a-dataset-001.xml"
    )
    assert file_found_in_extracted_zip(context, "iati-data-main/metadata/test_foundation_a.json")
    assert file_found_in_extracted_zip(
        context, "iati-data-main/metadata/test_foundation_a/test_foundation_a-dataset-001.json"
    )


def test_codeforiati_zip_content_for_download_fail_no_cached(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    run_checker_then_zipper_download_fail(context)

    download_and_unpack_zip_to_tmp_unpack_folder(context, "code-for-iati-data-download.zip")

    assert not file_found_in_extracted_zip(context, "iati-data/datasets-minimal.json")
    assert not file_found_in_extracted_zip(context, "iati-data/datasets-full.json")
    assert not file_found_in_extracted_zip(context, "iati-data/reporting-orgs.json")
    assert file_found_in_extracted_zip(context, "iati-data-main/metadata.json")
    assert file_found_in_extracted_zip(
        context, "iati-data-main/data/test_foundation_a/test_foundation_a-dataset-001.xml"
    )
    assert file_found_in_extracted_zip(context, "iati-data-main/metadata/test_foundation_a.json")
    assert file_found_in_extracted_zip(
        context, "iati-data-main/metadata/test_foundation_a/test_foundation_a-dataset-001.json"
    )

    assert (
        os.path.getsize(
            os.path.join(
                context["TEST_TMP_ZIP_UNPACK"],
                "iati-data-main/data/test_foundation_a/test_foundation_a-dataset-001.xml",
            )
        )
        == 0
    )


def run_checker_then_zipper(context, registry_url: str, datasets_in_bds: dict, datasets_in_zip: dict):
    context["DATA_REGISTRY_BASE_URL"] = registry_url
    checker_run(context, datasets_in_bds)
    zipper_run(context, datasets_in_zip, datasets_in_bds, get_reporting_orgs_in_bds(context))


def run_checker_then_zipper_once(
    context, registry_url: str = "http://localhost:3000/ckan-registration/datasets-01-1-dataset"
):
    context["DATA_REGISTRY_BASE_URL"] = registry_url
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    datasets_in_zip = {}
    zipper_run(context, datasets_in_zip, datasets_in_bds, get_reporting_orgs_in_bds(context))


def run_checker_then_zipper_download_fail(context):
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-03-1-dataset-404"
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    datasets_in_zip = {}
    zipper_run(context, datasets_in_zip, datasets_in_bds, get_reporting_orgs_in_bds(context))


def run_checker_then_zipper_download_fail_but_cached(context):
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-01-1-dataset"
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    # this is same dataset as above, only with a 404 URL
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-03-1-dataset-404"
    checker_run(context, datasets_in_bds)

    datasets_in_zip = {}
    zipper_run(context, datasets_in_zip, datasets_in_bds, get_reporting_orgs_in_bds(context))


def download_and_unpack_zip_to_tmp_unpack_folder(context, zip_name: str = "iati-data.zip"):
    dest_filename = os.path.join(context["TEST_TMP_ZIP_UNPACK"], "downloaded.zip")

    response = requests.get(f"{context["WEB_BASE_URL"]}/{context["AZURE_STORAGE_BLOB_CONTAINER_NAME"]}/{zip_name}")
    response.raise_for_status()

    with open(dest_filename, "wb") as f:
        f.write(response.content)

    zf = zipfile.ZipFile(dest_filename)
    zf.extractall(context["TEST_TMP_ZIP_UNPACK"])


def file_found_in_extracted_zip(context, filename: str) -> bool:
    return os.path.exists(os.path.join(context["TEST_TMP_ZIP_UNPACK"], filename))
