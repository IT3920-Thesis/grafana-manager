import psycopg2
from psycopg2.extensions import connection
import logging
from typing import List, Tuple, Optional

_LOG = logging.getLogger(__name__)


def connect(dbname: str, user: str, host: str, password: str) -> connection:
    try:
        conn = psycopg2.connect(f"dbname={dbname} user={user} host={host} password={password}")
        _LOG.info(f"Connection to {dbname} established")
        return conn
    except Exception as e:
        _LOG.exception("Could not connect to db")
        raise e


def query_db_conn(conn: connection, query: str, query_params: Optional[Tuple]) -> List:
    try:
        # use try-finally because `with` statement doesn't close connections
        # https://www.psycopg.org/docs/usage.html#with-statement
        curs = conn.cursor()
        try:
            curs.execute(query, query_params)
            res = curs.fetchall()
        finally:
            curs.close()
    except Exception as e:
        _LOG.exception("Querying db connection failed")
        raise e

    return res


def get_authors_by_repo_id(conn: connection, repo_id: int) -> List:
    query = "SELECT DISTINCT author_email FROM changecontribution WHERE repository_id=(%s);"
    query_params = (repo_id,)
    return query_db_conn(conn, query, query_params)


def get_all_repositories(conn: connection) -> List:
    query = "SELECT DISTINCT group_id, repository_id FROM changecontribution;"
    return query_db_conn(conn, query, query_params=None)
