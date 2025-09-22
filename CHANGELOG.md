# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

### Changed

### Fixed

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
