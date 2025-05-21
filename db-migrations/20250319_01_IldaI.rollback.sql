--
-- depends: 20250225_01_quLDd

alter table iati_datasets
    rename column most_recent_head_attempt_datetime to last_head_attempt;

alter table iati_datasets
    rename column most_recent_head_attempt_http_status to last_head_http_status;

alter table iati_datasets
    rename column most_recent_head_attempt_error_details to head_error_message;

alter table iati_datasets
    DROP COLUMN IF EXISTS most_recent_head_attempt_server_headers;
