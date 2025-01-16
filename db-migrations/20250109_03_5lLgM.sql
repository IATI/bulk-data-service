--
-- depends: 20250109_02_CDARS
--

alter table iati_datasets
    drop column if exists registration_service_publisher_metadata;

alter table iati_datasets
    rename column publisher_id to reporting_org_id;

alter table iati_datasets
    rename column publisher_name to reporting_org_short_name;

alter table iati_datasets
    rename column name to short_name;
