--
-- depends: 20250319_02_IXOsJ

alter table iati_datasets
    add license_id varchar;

comment on column iati_datasets.license_id is 'the license id, e.g., ''cc-by'' or ''uk-ogl''';

alter table iati_datasets
    drop column if exists type;

alter table iati_datasets
    drop column if exists content_modified;

alter table iati_datasets
    drop column if exists content_modified_excluding_generated_timestamp;
