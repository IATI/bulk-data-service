import json
import os
import zipfile

from bulk_data_service.checker import checker_run
from bulk_data_service.zipper import zipper_run
from helpers.helpers import get_and_clear_up_context, get_number_xml_files_in_working_dir  # noqa: F401
from utilities.db import get_reporting_orgs_in_bds


def test_dataset_saved_for_download_success(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    run_checker_then_zipper_download_ok(context)

    assert get_number_xml_files_in_working_dir(context) == 1
    assert os.path.exists("{}{}".format(
        context["ZIP_WORKING_DIR"],
        "/iati-data/datasets/test_foundation_a/test_foundation_a-dataset-001.xml")) is True


def test_dataset_not_saved_for_download_fail_and_no_cache(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    run_checker_then_zipper_download_fail(context)

    assert get_number_xml_files_in_working_dir(context) == 0


def test_dataset_saved_for_download_fail_but_cached(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    run_checker_then_zipper_download_fail_but_cached(context)

    assert get_number_xml_files_in_working_dir(context) == 1
    assert os.path.exists("{}{}".format(
        context["ZIP_WORKING_DIR"],
        "/iati-data/datasets/test_foundation_a/test_foundation_a-dataset-001.xml")) is True


def test_publisher_metadata_saved_for_failed_metadata_dl(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    run_checker_then_zipper_download_ok(context)

    assert os.path.exists(context["ZIP_WORKING_DIR"] + "-2/iati-data-main/metadata/test_foundation_a.json") is True


def test_publisher_metadata_saved_for_successful_metadata_dl(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-05-1-dataset-updated"
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    datasets_in_zip = {}
    zipper_run(context, datasets_in_zip, datasets_in_bds, get_reporting_orgs_in_bds(context))

    assert os.path.exists(context["ZIP_WORKING_DIR"] + "-2/iati-data-main/metadata/test_foundation_a.json") is True


def test_publisher_metadata_content_for_successful_metadata_dl(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-05-1-dataset-updated"
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    datasets_in_zip = {}
    zipper_run(context, datasets_in_zip, datasets_in_bds, get_reporting_orgs_in_bds(context))

    with open(context["ZIP_WORKING_DIR"] + "-2/iati-data-main/metadata/test_foundation_a.json", "r") as f:
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

    with open(context["ZIP_WORKING_DIR"] + "-2/iati-data-main/metadata/test_foundation_a/test_foundation_a-dataset-001-newname.json", "r") as f:
        assert f.read() == json.dumps(
            {
                "id": "c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159",
                "license_id": "uk-ogl",
                "license_title": "UK Open Government Licence (OGL)",
                "name": "test_foundation_a-dataset-001-newname",
                "organization": {"id": "ea055d99-f7e9-456f-9f99-963e95493c1b", "name": "test_foundation_a", },
                "resources": [{"url": "http://localhost:3000/not_found"}],
                "extras": [],
                "tags": [],
                "groups": [],
                "users": [],
            }
        )


def test_bds_zip_content_for_download_success(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    run_checker_then_zipper_download_ok(context)

    bds_zip_filename = context["ZIP_WORKING_DIR"] + "-1/iati-data.zip"

    assert os.path.exists(bds_zip_filename) is True

    bds_zip_file = zipfile.ZipFile(bds_zip_filename)

    filelist = bds_zip_file.namelist()

    assert ("iati-data/datasets-minimal.json" in filelist) is True
    assert ("iati-data/datasets-full.json" in filelist) is True
    assert ("iati-data/reporting-orgs.json" in filelist) is True
    assert ("iati-data/datasets/test_foundation_a/test_foundation_a-dataset-001.xml" in filelist) is True


def test_bds_zip_content_for_download_fail_but_cached(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    run_checker_then_zipper_download_fail_but_cached(context)

    bds_zip_filename = context["ZIP_WORKING_DIR"] + "-1/iati-data.zip"

    assert os.path.exists(bds_zip_filename) is True

    bds_zip_file = zipfile.ZipFile(bds_zip_filename)

    filelist = bds_zip_file.namelist()

    assert ("iati-data/datasets-minimal.json" in filelist) is True
    assert ("iati-data/datasets-full.json" in filelist) is True
    assert ("iati-data/reporting-orgs.json" in filelist) is True
    assert ("iati-data/datasets/test_foundation_a/test_foundation_a-dataset-001.xml" in filelist) is True


def test_bds_zip_content_for_download_fail_no_cached(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    run_checker_then_zipper_download_fail(context)

    bds_zip_filename = context["ZIP_WORKING_DIR"] + "-1/iati-data.zip"

    assert os.path.exists(bds_zip_filename) is True

    bds_zip_file = zipfile.ZipFile(bds_zip_filename)

    filelist = bds_zip_file.namelist()

    assert ("iati-data/datasets-minimal.json" in filelist) is True
    assert ("iati-data/datasets-full.json" in filelist) is True
    assert ("iati-data/reporting-orgs.json" in filelist) is True
    assert ("iati-data/datasets/test_foundation_a/test_foundation_a-dataset-001.xml" in filelist) is False


def test_codeforiati_zip_content_for_download_success(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    run_checker_then_zipper_download_ok(context)

    bds_zip_filename = context["ZIP_WORKING_DIR"] + "-2/code-for-iati-data-download.zip"

    assert os.path.exists(bds_zip_filename) is True

    bds_zip_file = zipfile.ZipFile(bds_zip_filename)

    filelist = bds_zip_file.namelist()

    assert ("iati-data/datasets-minimal.json" in filelist) is False
    assert ("iati-data/datasets-full.json" in filelist) is False
    assert ("iati-data/reporting-orgs.json" in filelist) is False
    assert ("iati-data-main/metadata.json" in filelist) is True
    assert ("iati-data-main/data/test_foundation_a/test_foundation_a-dataset-001.xml" in filelist) is True
    assert ("iati-data-main/metadata/test_foundation_a.json" in filelist) is True
    assert ("iati-data-main/metadata/test_foundation_a/test_foundation_a-dataset-001.json" in filelist) is True


def test_codeforiati_zip_content_for_download_fail_but_cached(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    run_checker_then_zipper_download_fail_but_cached(context)

    bds_zip_filename = context["ZIP_WORKING_DIR"] + "-2/code-for-iati-data-download.zip"

    assert os.path.exists(bds_zip_filename) is True

    bds_zip_file = zipfile.ZipFile(bds_zip_filename)

    filelist = bds_zip_file.namelist()

    assert ("iati-data/datasets-minimal.json" in filelist) is False
    assert ("iati-data/datasets-full.json" in filelist) is False
    assert ("iati-data/reporting-orgs.json" in filelist) is False
    assert ("iati-data-main/metadata.json" in filelist) is True
    assert ("iati-data-main/data/test_foundation_a/test_foundation_a-dataset-001.xml" in filelist) is True
    assert ("iati-data-main/metadata/test_foundation_a.json" in filelist) is True
    assert ("iati-data-main/metadata/test_foundation_a/test_foundation_a-dataset-001.json" in filelist) is True


def test_codeforiati_zip_content_for_download_fail_no_cached(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    run_checker_then_zipper_download_fail(context)

    bds_zip_filename = context["ZIP_WORKING_DIR"] + "-2/code-for-iati-data-download.zip"

    assert os.path.exists(bds_zip_filename) is True

    bds_zip_file = zipfile.ZipFile(bds_zip_filename)

    fileinfolist = bds_zip_file.infolist()
    filelist = [fileinfo.filename for fileinfo in fileinfolist]

    assert ("iati-data/datasets-minimal.json" in filelist) is False
    assert ("iati-data/datasets-full.json" in filelist) is False
    assert ("iati-data/reporting-orgs.json" in filelist) is False
    assert ("iati-data-main/metadata.json" in filelist) is True
    assert ("iati-data-main/data/test_foundation_a/test_foundation_a-dataset-001.xml" in filelist) is True
    assert ("iati-data-main/metadata/test_foundation_a.json" in filelist) is True
    assert ("iati-data-main/metadata/test_foundation_a/test_foundation_a-dataset-001.json" in filelist) is True

    fileinfoxml = list(filter(lambda f: f.filename == "iati-data-main/data/test_foundation_a/test_foundation_a-dataset-001.xml", fileinfolist))[0]
    assert fileinfoxml.file_size == 0


def run_checker_then_zipper_download_ok(context):
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-01-1-dataset"
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
