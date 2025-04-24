--
-- depends: 20250319_03_NBaZ1

alter table iati_datasets
    rename column last_known_good_dataset_hash to hash;

alter table iati_datasets
    rename column last_known_good_dataset_hash_excluding_generated_timestamp to hash_excluding_generated_timestamp;

alter table iati_datasets
    rename column last_known_good_dataset_downloaded to last_successful_download;

alter table iati_datasets
    rename column last_known_good_dataset_verified_on_server to last_verified_on_server;

alter table iati_datasets
    rename column last_known_good_dataset_content_length to download_content_length;

alter table iati_datasets
    rename column last_known_good_dataset_initial_contents to download_initial_contents;

alter table iati_datasets
    rename column last_known_good_dataset_server_header_last_modified to server_header_last_modified;

alter table iati_datasets
    rename column last_known_good_dataset_server_header_etag to server_header_etag;

alter table iati_datasets
    drop column if exists last_known_good_dataset_source_url;
