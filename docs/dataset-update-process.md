# Dataset update process

- Get the list of datasets from the Registry.

- Remove any datasets that were previously registered but are now no longer in the list.

- For each dataset:

  1. If the dataset is new, mark as requiring full download attempt.

  1. If the source URL has changed, mark as requiring full download attempt.

  1. If the dataset is not new and `source_url` is unchanged, issue a `HEAD` request on the dataset's `source_url` and then:

     1. If the `ETag` header exists and its value has changed, mark as requiring full download attempt.

     1. If the `Last-Modified` header exists and has its value has changed, mark as requiring full download attempt.

     1. If the server refuses the `HEAD` request, then:

        1. If the dataset was successfully downloaded in the last 6 hours, update `cached_dataset_verified_on_server` and move to next dataset.

        1. If the dataset was not successfully downloaded in the last 6 hours, mark as requiring full download attempt.

  1. If the dataset last successful download (`cached_dataset_downloaded`) is before `CURRENT_TIME - (FORCE_REDOWNLOAD_AFTER_HOURS - RANDOM_HOURS)`, where `RANDOM_HOURS` is between 0 and 8, mark as requiring full download attempt.

  1. Attempt a full download of dataset if it has been marked as requiring such.
