--
-- depends: 20250826_01_8ipcJ

alter table iati_datasets
    add last_known_good_dataset_cached_dataset_xml_url varchar;

comment on column iati_datasets.last_known_good_dataset_cached_dataset_xml_url
    is 'the url of the cached XML version of the dataset';

alter table iati_datasets
    add last_known_good_dataset_cached_dataset_xml_etag varchar;

comment on column iati_datasets.last_known_good_dataset_cached_dataset_xml_etag
    is 'the ETag of the cached XML version of the dataset on Azure blob storage';

alter table iati_datasets
    add last_known_good_dataset_cached_dataset_zip_url varchar;

comment on column iati_datasets.last_known_good_dataset_cached_dataset_xml_url
    is 'the url of the cached ZIP version of the dataset';

alter table iati_datasets
    add last_known_good_dataset_cached_dataset_zip_etag varchar;

comment on column iati_datasets.last_known_good_dataset_cached_dataset_xml_etag
    is 'the ETag of the cached ZIP version of the dataset on Azure blob storage';

alter table iati_datasets
    add most_recent_get_attempt_error_occurred boolean;

comment on column iati_datasets.most_recent_get_attempt_error_occurred
    is 'indicates whether the last GET attempt encountered an error retreiving an IATI XML file';

alter table iati_datasets
    add most_recent_head_attempt_error_occurred boolean;

comment on column iati_datasets.most_recent_head_attempt_error_occurred
    is 'indicates whether the last HEAD attempt encountered an error';

alter table iati_datasets
    add registration_service_metadata_refreshed_datetime timestamp with time zone;

comment on column iati_datasets.registration_service_metadata_refreshed_datetime
    is 'the datetime at which the dataset registration data was last refreshed (via refresh cycle or MQ)';

alter table iati_datasets
    drop column if exists most_recent_get_attempt_server_headers;

alter table iati_datasets
    drop column if exists most_recent_head_attempt_server_headers;

alter table iati_reporting_orgs
    drop column if exists number_of_published_datasets;

alter table iati_reporting_orgs
    add registration_service_metadata_refreshed_datetime timestamp with time zone;

comment on column iati_reporting_orgs.registration_service_metadata_refreshed_datetime
    is 'the datetime at which the reporting org registration data was last refreshed (via refresh cycle or MQ)';
