--
-- depends: 20250319_01_IldaI

alter table iati_datasets
    rename column most_recent_get_attempt_datetime to last_download_attempt;

alter table iati_datasets
    rename column most_recent_get_attempt_http_status to last_download_http_status;

alter table iati_datasets
    rename column most_recent_get_attempt_error_details to download_error_message;

alter table iati_datasets
    drop column if exists most_recent_get_attempt_server_headers;
