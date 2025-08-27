--
-- depends: 20250822_01_VptWi

alter table iati_reporting_orgs
    rename column iati_identifier to organisation_identifier;
