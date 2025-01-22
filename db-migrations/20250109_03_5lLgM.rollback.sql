--
-- depends: 20250109_02_CDARS
--

ALTER TABLE
    iati_datasets
ADD
    registration_service_publisher_metadata VARCHAR;

alter table iati_datasets
    rename column reporting_org_id to publisher_id;

alter table iati_datasets
    rename column reporting_org_short_name to publisher_name;

alter table iati_datasets
    rename column short_name to name;
