--
-- depends: 20240531_01_iY5Qa
--
ALTER TABLE
    iati_datasets
ADD
    registration_service_dataset_metadata VARCHAR;

COMMENT ON COLUMN iati_datasets.registration_service_dataset_metadata IS 'the original dataset metadata record from the data registration service';

ALTER TABLE
    iati_datasets
ADD
    registration_service_publisher_metadata VARCHAR;

COMMENT ON COLUMN iati_datasets.registration_service_publisher_metadata IS 'the original publisher metadata record from the data registration service';

ALTER TABLE
    iati_datasets
ADD
    registration_service_name VARCHAR;

COMMENT ON COLUMN iati_datasets.registration_service_name IS 'the name of the data registration service';