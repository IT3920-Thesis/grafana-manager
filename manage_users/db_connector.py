import psycopg2
from psycopg2.extensions import connection
import logging
from dotenv import dotenv_values
from typing import List

config = dotenv_values(".env")
_LOG = logging.getLogger(__name__)


def connect(dbname: str, user: str, host: str, password: str) -> connection:
    try:
        return psycopg2.connect(f"dbname={dbname} user={user} host={host} password={password}")
    except Exception as e:
        _LOG.exception("Could not connect to db")
        raise e


def query_db_conn(conn: connection, query: str):
    try:
        curs = conn.cursor()
        try:
            curs.execute(query)
            res = curs.fetchall()
        finally:
            curs.close()
    except Exception as e:
        _LOG.exception("Querying db connection failed")
        raise e

    return res


def get_authors_by_repo_id(conn: connection, repo_id: int) -> List:
    query = f"SELECT DISTINCT(author_email) FROM changecontribution WHERE repository_id='{repo_id}';"
    return query_db_conn(conn, query)


conn = connect(dbname=config["DB_NAME"], user=config["DB_USER"], host=config["DB_HOST"], password=config["DB_HOST"])
print(get_authors_by_repo_id(conn, 1021))

