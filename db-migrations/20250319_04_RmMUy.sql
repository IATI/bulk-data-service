--
-- depends: 20250319_03_NBaZ1

alter table iati_datasets
    rename column hash to last_known_good_dataset_hash;

alter table iati_datasets
    rename column hash_excluding_generated_timestamp to last_known_good_dataset_hash_excluding_generated_timestamp;

alter table iati_datasets
    rename column last_successful_download to last_known_good_dataset_downloaded;

alter table iati_datasets
    rename column last_verified_on_server to last_known_good_dataset_verified_on_server;

alter table iati_datasets
    rename column download_content_length to last_known_good_dataset_content_length;

alter table iati_datasets
    rename column download_initial_contents to last_known_good_dataset_initial_contents;

alter table iati_datasets
    rename column server_header_last_modified to last_known_good_dataset_server_header_last_modified;

alter table iati_datasets
    rename column server_header_etag to last_known_good_dataset_server_header_etag;

alter table iati_datasets
    add last_known_good_dataset_source_url varchar;

-- column reordering is not supported iati_datasets.last_known_good_dataset_source_url

comment on column iati_datasets.last_known_good_dataset_source_url is 'the url from which the last known good dataset was successfully downloaded ';
