--
-- depends: 20250827_01_Dt6Ow

alter table iati_datasets
    alter column most_recent_head_attempt_error_occurred set default false;

alter table iati_datasets
    alter column most_recent_get_attempt_error_occurred set default false;

update iati_datasets
    set most_recent_head_attempt_error_occurred = false
    where most_recent_head_attempt_error_occurred is null;

update iati_datasets
    set most_recent_get_attempt_error_occurred = false
    where most_recent_get_attempt_error_occurred is null;
