# Bulk Data Service Update Cycle

- Get the list of reporting orgs from the Registry.

- Get the full metadata for each reporting org.

- Get the list of datasets from the Registry.

- Remove any datasets from the DB and the IATI Cache that were previously
  registered but are now no longer in the list.

- Remove any reporting orgs from the Bulk Data Service database that no longer
  appear in the Registry.

- For each remaining dataset:

  1. Update the dataset's `last_update_check` date/time stamp.

  1. If the dataset has been downloaded within the last 24 hours and the
     `source_url` is unchanged, issue a `HEAD` request.

  1. If there was an error with the `HEAD` request but the file was successfully
     downloaded within the last 6 hours, then update the fields on
     `most_recent_head_request` and exit.

  1. If the `HEAD` request succeeded and the ETag and Last-Modified headers have
     remained the same as they were, then update the fields in
     `most_recent_head_request` and exit.

  1. If there was an error with the `HEAD` request and the file was
     successfully downloaded more than 6 hours ago, or if the `HEAD` request
     succeeded and there were any changes in ETag or Last-Modified header, then
     proceed to attempt full download.

  1. Attempt to download the dataset.

  1. If the download failed for any reason, then update fields in
     `most_recent_get_request` and exit.

  1. Extract the first 6000 characters of the dataset and check if the downloaded file has an opening IATI XML element.

  1. If the dataset doesn't have an opening IATI XML element, then update fields in `most_recent_get_attempt` and exit.

  1. If the dataset does have an opening IATI XML element, then generate the
     IATI hashes and attempt to upload the dataset to the IATI dataset cache,
     both as an XML file and as individual ZIP file.

  1. Update all the fields on the `most_recent_get_attempt` and `last_known_good_dataset` objects and exit.
