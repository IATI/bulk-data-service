--
-- depends: 20240531_01_iY5Qa
ALTER TABLE
    iati_datasets DROP COLUMN IF EXISTS registration_service_dataset_metadata;

ALTER TABLE
    iati_datasets DROP COLUMN IF EXISTS registration_service_publisher_metadata;

ALTER TABLE
    iati_datasets DROP COLUMN IF EXISTS registration_service_name;