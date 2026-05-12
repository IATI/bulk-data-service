alter table iati_datasets
    alter column most_recent_head_attempt_error_occurred drop default;

alter table iati_datasets
    alter column most_recent_get_attempt_error_occurred drop default;
