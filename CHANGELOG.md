# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

### Changed

### Fixed

### Removed

## [1.4.3] - 2026-03-10

### Changed

- Updated website to link to docs and to match naming of this service as it
  appears on other websites.
- Change name of service in page.
- Upgraded the design system.

## [1.4.2] - 2025-12-01

### Changed

- Modified so that the BDS only pulls public datasets from the Registry.

## [1.4.1]

### Changed

- Modified so that the BDS only pulls reporting orgs marked as discoverable on
  the Registry.

## [1.4.0]

### Added

- Test infrastructure, setup, and new tests for pulling dataset, reporting org
  lists from SuiteCRM.
- Code to pull the dataset and reporting org lists from SuiteCRM.

### Fixed

- Deleted datasets are only deleteed from Azure blob storage if there is a
  cached copy stored.

## [1.3.4]

### Added

- Added a verify ZIP stage which attempts to unzip the entire ZIP file, and if
  that fails, it forces a full re-download of all the XML files and then
  re-attempts the creation of the ZIP.

### Changed

- To verify the ZIP we have to extract it all. This requires a lot of space, and
  it means we can no longer just leave the XML files for building the ZIP on
  disk in between runs, because Azure Container Instances only give ~50 Gb of
  disk space, and it's not configurable. So, the XML files for each of the ZIP
  files and the ZIP files themselves are now removed from disk after being
  uploaded to Azure. But this has meant the automated tests can't just inspect
  these folders to check they contain the correct content - the automated tests
  now need to download the appropriate ZIP and unpack it. This is why there are
  changes to all the ZIP tests.

### Fixed

- Fixed an issue whereby when an update was made to the dataset's shortname,
  the dataset was not being updated in the ZIP with the new name.

### Removed

## [1.3.3]

### Added

- Design system has been upgraded to the latest version, thanks to @BibianaC.
- Environment variables `REDOWNLOAD_FROM_NON_HEAD_SERVERS_AFTER_HOURS`, which
  allows configuration of how long to redownload from servers that don't support
  `HEAD` requests, `DATASET_HEAD_TIMEOUT` and `DATASET_GET_TIMEOUT`, which are
  self-explanatory.
- New DB columns to store when the dataset and reporting_org metadata was last
  refreshed.
- Detailed explanation to the `.env-example`.

### Changed

- Updated index outputs to match new specs.
- Refactored much of the code that converts between native DB record format and
  the data transfer objects that come from/are sent to the message queue.

### Fixed

- `dataset_updater.py/add_or_update_dataset_batch()` now attempts to reconnect
  to the database if the connection is droped / fails.

### Removed

## [1.1.6] - 2025-08-21

### Added

- Improved documentation of update process.
- Added background message processing from Azure Service Bus (not yet setup on
  running systems).

### Fixed

- Fixed bug in IATI XML detection.

## [1.1.5] - 2025-07-30

### Added

- Added a foregin key from the `iati_datasets` table to the
  `iati_reporting_orgs` table.

## [1.1.4] - 2025-07-15

### Fixed

- Fixed the `http_status` field not being blanked out when it should have been.
