--
-- depends: 20250826_01_8ipcJ

alter table iati_datasets
    drop column last_known_good_dataset_cached_dataset_xml_url;

alter table iati_datasets
    drop column last_known_good_dataset_cached_dataset_xml_etag;

alter table iati_datasets
    drop column last_known_good_dataset_cached_dataset_zip_url;

alter table iati_datasets
    drop column last_known_good_dataset_cached_dataset_zip_etag;

alter table iati_datasets
    drop column most_recent_get_attempt_error_occurred;

alter table iati_datasets
    drop column most_recent_head_attempt_error_occurred;

alter table iati_datasets
    drop column if exists registration_service_metadata_refreshed_datetime;

alter table iati_datasets
    add most_recent_get_attempt_server_headers varchar;

alter table iati_datasets
    add most_recent_head_attempt_server_headers varchar;

alter table iati_reporting_orgs
    add number_of_published_datasets int;

alter table iati_reporting_orgs
    drop column if exists registration_service_metadata_refreshed_datetime;