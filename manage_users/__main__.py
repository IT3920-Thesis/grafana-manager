from manage_users.api import auth, create_user, create_team, add_user_to_team
from manage_users.models import Team, User
from manage_users.db_connector import connect, get_all_repositories, get_authors_by_repo_id
import logging
from typing import Dict

_LOG = logging.getLogger(__name__)


def get_repos_and_authors() -> Dict:
    conn = connect(dbname="gitlabstats", user="gitlabstats", host="localhost", password="somepassword")

    try:
        repos = dict()
        for repo_name, repo_id in get_all_repositories(conn):
            repo_authors = get_authors_by_repo_id(conn, repo_id)
            repos[repo_id] = {
                "name": repo_name,
                "author_emails": repo_authors
            }

        return repos
    finally:
        conn.close()


def main() -> None:

    GRAFANA_API = auth(host='localhost:3000', username="admin", password="admin")
    repos = get_repos_and_authors()
    for repo_id, repo in repos.items():
        repo_name = repo['name']
        authors = repo['author_emails']

        grafana_team = create_team(GRAFANA_API, team=Team({
            "name": f"{repo_name}-{repo_id}"
        }))
        grafana_team_id = grafana_team['teamId']

        for author in authors:
            print(author[0])
            user = create_user(GRAFANA_API, User({
                "name": author[0],
                "email": author[0],
                "password": "somepassword"
            }))
            print(user)
            user_id = user['id']
            add_user_to_team(GRAFANA_API, user_id=user_id, team_id=grafana_team_id)


if __name__ == "__main__":
    main()
