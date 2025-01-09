import uuid

from utilities.db import get_db_connection, insert_or_update_organisation, remove_organisation_from_db


def add_or_update_organisations(context: dict, registered_organisations: dict[uuid.UUID, dict]):

    db_conn = get_db_connection(context)

    for organisation in registered_organisations.values():
        insert_or_update_organisation(db_conn, organisation)

    db_conn.close()


def remove_deleted_organisations_from_bds(
    context: dict, organisations_in_bds: dict[uuid.UUID, dict], registered_organisations: dict[uuid.UUID, dict]
):

    db_conn = get_db_connection(context)

    for organisation_uuid_in_bds in organisations_in_bds:
        if organisation_uuid_in_bds not in registered_organisations:
            remove_organisation_from_db(db_conn, organisation_uuid_in_bds)

    db_conn.close()
