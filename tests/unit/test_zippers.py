import datetime
import errno
import os
import uuid
import zipfile
from unittest import mock

import pytest

from bulk_data_service.zippers import CodeforIATILegacyZipper, IATIBulkDataServiceZipper


def get_zipper(zipper_class, working_dir):
    return zipper_class(mock.Mock(), str(working_dir), {}, {}, {})


def create_zip_source_tree(zipper):
    """Creates the directory tree which zip() archives, containing a single XML file."""
    datasets_dir = os.path.join(zipper.zip_source_dir, "datasets", "test_foundation_a")

    os.makedirs(datasets_dir, exist_ok=True)

    with open(os.path.join(datasets_dir, "test_foundation_a-dataset-001.xml"), "w") as xml_file:
        xml_file.write("<iati-activities></iati-activities>")


def get_zipper_with_zip_created(tmp_path):
    zipper = get_zipper(IATIBulkDataServiceZipper, tmp_path)

    create_zip_source_tree(zipper)

    zipper.zip()

    return zipper


@pytest.mark.parametrize(
    "zipper_class,expected_dir_name",
    [(IATIBulkDataServiceZipper, "iati-data"), (CodeforIATILegacyZipper, "iati-data-main")],
)
def test_zip_source_dir_is_the_zips_internal_directory(zipper_class, expected_dir_name, tmp_path):

    zipper = get_zipper(zipper_class, tmp_path)

    assert zipper.zip_source_dir == os.path.join(str(tmp_path), expected_dir_name)


def test_clean_zip_source_dir_removes_source_but_leaves_zip(tmp_path):

    zipper = get_zipper_with_zip_created(tmp_path)

    zipper.clean_zip_source_dir()

    assert os.path.exists(zipper.zip_source_dir) is False
    assert os.path.exists(zipper.get_zip_local_pathname()) is True


def test_clean_zip_source_dir_when_source_already_gone(tmp_path):

    zipper = get_zipper(IATIBulkDataServiceZipper, tmp_path)

    zipper.clean_zip_source_dir()

    assert os.path.exists(zipper.zip_source_dir) is False


def test_valid_zip_created_true_and_verify_dir_removed(tmp_path):

    zipper = get_zipper_with_zip_created(tmp_path)

    zipper.clean_zip_source_dir()

    assert zipper.valid_zip_created() is True
    assert os.path.exists(zipper.verify_dir) is False


def test_valid_zip_created_false_for_truncated_zip(tmp_path):

    zipper = get_zipper_with_zip_created(tmp_path)

    zipper.clean_zip_source_dir()

    with open(zipper.get_zip_local_pathname(), "r+b") as zip_file:
        zip_file.truncate(12)

    assert zipper.valid_zip_created() is False
    assert os.path.exists(zipper.verify_dir) is False


def test_valid_zip_created_false_for_missing_zip(tmp_path):

    zipper = get_zipper(IATIBulkDataServiceZipper, tmp_path)

    assert zipper.valid_zip_created() is False


def get_code_for_iati_zipper_for_one_dataset(tmp_path, has_download: bool):
    dataset_id = uuid.uuid4()

    datasets_in_bds = {
        dataset_id: {
            "id": dataset_id,
            "short_name": "test_foundation_a-dataset-001",
            "reporting_org_short_name": "test_foundation_a",
            "last_known_good_dataset_downloaded": (datetime.datetime.now(datetime.UTC) if has_download else None),
        }
    }

    return CodeforIATILegacyZipper(mock.Mock(), str(tmp_path), {}, datasets_in_bds, {})


@pytest.mark.parametrize("has_download", [True, False])
def test_placeholder_file_created_when_dataset_has_no_xml_in_working_dir(has_download, tmp_path):
    """The Code for IATI ZIP holds a file for every dataset, empty where there is no data. A
    dataset recorded as having a good download can still have no XML file in the working dir,
    because a download which is not found in Azure is logged and skipped, and if it is the only
    dataset for its publisher then nothing else creates the publisher's directory."""

    zipper = get_code_for_iati_zipper_for_one_dataset(tmp_path, has_download)

    zipper.create_empty_files_for_non_downloadable_datasets()

    placeholder = os.path.join(
        str(tmp_path), "iati-data-main", "data", "test_foundation_a", "test_foundation_a-dataset-001.xml"
    )

    assert os.path.exists(placeholder) is True
    assert os.path.getsize(placeholder) == 0


def test_existing_xml_is_not_replaced_by_placeholder(tmp_path):

    zipper = get_code_for_iati_zipper_for_one_dataset(tmp_path, has_download=True)

    data_dir = os.path.join(str(tmp_path), "iati-data-main", "data", "test_foundation_a")
    os.makedirs(data_dir)
    with open(os.path.join(data_dir, "test_foundation_a-dataset-001.xml"), "w") as xml_file:
        xml_file.write("<iati-activities></iati-activities>")

    zipper.create_empty_files_for_non_downloadable_datasets()

    assert os.path.getsize(os.path.join(data_dir, "test_foundation_a-dataset-001.xml")) > 0


def test_valid_zip_created_false_and_cleans_up_when_disk_full(tmp_path):
    """The failure this guards against: previously an ENOSPC during the verification extract
    escaped the zipper run, leaving the part-extracted copy on the disk which had just filled."""

    zipper = get_zipper_with_zip_created(tmp_path)

    zipper.clean_zip_source_dir()

    def raise_no_space_left(_, path):
        os.makedirs(path, exist_ok=True)
        raise OSError(errno.ENOSPC, "No space left on device")

    with mock.patch.object(zipfile.ZipFile, "extractall", raise_no_space_left):
        assert zipper.valid_zip_created() is False

    assert os.path.exists(zipper.verify_dir) is False
