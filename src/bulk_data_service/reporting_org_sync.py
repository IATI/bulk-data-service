import uuid

from config.bds_context import BDSContext
from utilities.db import get_db_connection, insert_or_update_reporting_org, remove_reporting_org_from_db


def add_or_update_reporting_orgs(context: BDSContext, registered_reporting_orgs: dict[uuid.UUID, dict]):

    db_conn = get_db_connection(context)

    for reporting_org in registered_reporting_orgs.values():
        insert_or_update_reporting_org(db_conn, reporting_org)

    db_conn.close()


def remove_deleted_reporting_orgs_from_bds(
    context: BDSContext, reporting_orgs_in_bds: dict[uuid.UUID, dict], registered_reporting_orgs: dict[uuid.UUID, dict]
):

    db_conn = get_db_connection(context)

    for reporting_org_uuid_in_bds in reporting_orgs_in_bds:
        if reporting_org_uuid_in_bds not in registered_reporting_orgs:
            remove_reporting_org_from_db(db_conn, reporting_org_uuid_in_bds)

    db_conn.close()
