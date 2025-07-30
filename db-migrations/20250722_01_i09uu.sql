--
-- depends: 20250605_01_Rsfu1

alter table iati_datasets
    add constraint iati_datasets___fk
        foreign key (reporting_org_id) references iati_reporting_orgs (id)
    on delete cascade;
