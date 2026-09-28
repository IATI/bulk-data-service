import errno
import os
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
