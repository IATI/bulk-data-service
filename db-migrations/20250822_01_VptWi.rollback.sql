--
-- depends: 20250722_01_i09uu

alter table iati_reporting_orgs
    drop column created_date;

alter table iati_reporting_orgs
    drop column data_portal_url;

alter table iati_reporting_orgs
    drop column default_licence_id;

alter table iati_reporting_orgs
    drop column description;

alter table iati_reporting_orgs
    drop column exclusions_policy_url;

alter table iati_reporting_orgs
    drop column first_publication_date;

alter table iati_reporting_orgs
    drop column hq_country;

alter table iati_reporting_orgs
    drop column number_of_published_datasets;

alter table iati_reporting_orgs
    drop column organisation_type;

alter table iati_reporting_orgs
    drop column region;

alter table iati_reporting_orgs
    drop column reporting_source_type;

alter table iati_reporting_orgs
    drop column website;
