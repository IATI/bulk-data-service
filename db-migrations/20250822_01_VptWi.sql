--
-- depends: 20250722_01_i09uu

alter table iati_reporting_orgs
    add created_date timestamp with time zone;

alter table iati_reporting_orgs
    add data_portal_url varchar;

alter table iati_reporting_orgs
    add default_licence_id varchar(32);

alter table iati_reporting_orgs
    add description varchar;

alter table iati_reporting_orgs
    add exclusions_policy_url varchar;

alter table iati_reporting_orgs
    add first_publication_date timestamp with time zone;

alter table iati_reporting_orgs
    add hq_country varchar(8);

alter table iati_reporting_orgs
    add number_of_published_datasets int;

alter table iati_reporting_orgs
    add organisation_type varchar(8);

alter table iati_reporting_orgs
    add region varchar(8);

alter table iati_reporting_orgs
    add reporting_source_type varchar(20);

alter table iati_reporting_orgs
    add website varchar;

