--
-- depends: 20250109_03_5lLgM
--

ALTER TABLE
    iati_datasets
ADD
    download_content_length INTEGER;


ALTER TABLE
    iati_datasets
ADD
    download_initial_contents VARCHAR;

