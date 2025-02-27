--
-- depends: 20250109_03_5lLgM
--


ALTER TABLE
    iati_datasets
 DROP COLUMN IF EXISTS
    download_content_length;


ALTER TABLE
    iati_datasets
 DROP COLUMN IF EXISTS
    download_initial_contents;
