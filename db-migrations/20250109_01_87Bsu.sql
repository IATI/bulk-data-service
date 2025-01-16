--
-- depends: 20240827_01_pVOLG
--

-- auto-generated definition
create table iati_organisations
(
    id                                          uuid    not null,
    short_name                                  varchar not null,
    iati_identifier                             varchar,
    human_readable_name                         varchar,
    registration_service_reporting_org_metadata varchar
);

comment on column iati_organisations.id is 'the UUID of the reporting organisation';

comment on column iati_organisations.short_name is 'the short id of the reporting organisation';

comment on column iati_organisations.iati_identifier is 'the IATI identifier of the reporting organisation';

comment on column iati_organisations.human_readable_name is 'the canonical human readable name of the reporting organisation';

comment on column iati_organisations.registration_service_reporting_org_metadata is 'the original reporting organisation metadata record from the data registration service';

alter table iati_organisations
    owner to bds;

create unique index iati_organisations_pk
    on iati_organisations (id);

