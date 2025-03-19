--
-- depends: 20250319_01_IldaI

alter table iati_datasets
    rename column last_download_attempt to most_recent_get_attempt_datetime;

alter table iati_datasets
    rename column last_download_http_status to most_recent_get_attempt_http_status;

alter table iati_datasets
    rename column download_error_message to most_recent_get_attempt_error_details;

alter table iati_datasets
    add most_recent_get_attempt_server_headers varchar;
