# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Errors are reported to Sentry, when a `SENTRY_DSN` is configured. Events are
  tagged with the environment, the app version, and which of the three
  operations they came from. Stack-frame variables are not sent, and the
  configuration variables which hold credentials are scrubbed by name, so that
  the app's credentials are not included in an event.

### Changed

- Exceptions which the service loops catch and retry are now logged with the
  exception attached, so that the traceback reaches the log and Sentry as one
  structured record rather than as separate messages. Previously the traceback
  was logged as a separate string, or printed to stdout.

- Errors about individual SuiteCRM records are marked with the class of alert
  they belong to, so that repeat occurrences accumulate on one Sentry issue
  instead of producing one issue per record. The log messages are unchanged.

### Fixed

### Removed

## [1.4.13] - 2026-08-27

### Added

 - Non-secret configuration variables are written to the log when the service
   starts.

### Changed

 - Azure blob service clients are now obtained from the service factory, which
   applies an explicit exponential retry policy rather than relying on the
   Azure SDK defaults.

## [1.4.12] - 2026-08-03

### Changed

 - Added a small meta JSON file for use by the landing page so that it can show
   the last updated timestamps without needing to access the full indices.

## [1.4.11] - 2026-07-29

### Changed

 - Updated licence codelist list with new licence code 'other'.

## [1.4.10] - 2026-07-27

### Changed

 - Expanded explanatory text, added 'Last updated: ' for the indices, and
   brought IATI footer up to date.
 - Pinned the Azure Service Bus emulator to version 1.1.2 in the local
   development and test docker compose setups, rather than tracking `latest`.

### Fixed

 - Fixed intermittent CI test failures caused by a race condition due to the
   tests sometimes starting before the Azure Service Bus emulator was ready: CI
   now waits for the emulator's health API before running the tests, and dumps
   the docker compose logs if the tests fail.

## [1.4.9] - 2026-05-25

### Fixed

 - Updated error handling for MQ sending so that any errors sending dataset
   check results doesn't cause checker loop to exit early.

## [1.4.8] - 2026-05-18

### Removed

 - Fixed IP deployment

## [1.4.7] - 2026-05-11

### Added

- Added back in the manual deploy script

### Fixed

- Fixed Azure deploy to use full resource identifiers for dedicated vnet & subnet

## [1.4.6] - 2026-05-11

### Changed

- Updated deploy to use dedicated vnet & subnet

### Fixed

- Added env var for the MQ topic name to the GitHub workflow.

## [1.4.5] - 2026-05-06

### Changed

- Updated IATI Design System to 4.9.0

### Fixed

- Bug where the dataset's cached URLs were not being blanked after dataset expiry. (Resolves #137)
- Bug where `most_recent_head_attempt.error_occurred` was being set to `null` instead of `false`. (Resolves #136).

## [1.4.4] - 2026-04-22

### Added

- Command line flag to enable processing of a single reporting org.

### Fixed

- Stop datasets from unapproved reporting orgs from being processed.

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
