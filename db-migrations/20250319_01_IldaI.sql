--
-- depends: 20250225_01_quLDd

alter table iati_datasets
    rename column last_head_attempt to most_recent_head_attempt_datetime;

alter table iati_datasets
    rename column last_head_http_status to most_recent_head_attempt_http_status;

alter table iati_datasets
    rename column head_error_message to most_recent_head_attempt_error_details;

alter table iati_datasets
    add most_recent_head_attempt_server_headers varchar;

