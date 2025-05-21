--
-- depends: 20250319_02_IXOsJ

alter table iati_datasets
    drop column if exists license_id;

alter table iati_datasets
    add type varchar default '' not null;

alter table iati_datasets
    add content_modified timestamp with time zone;

alter table iati_datasets
    add content_modified_excluding_generated_timestamp timestamp with time zone;
