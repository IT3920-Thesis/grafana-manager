import logging
from typing import Dict

import dotenv

from manage_users.api.gitlab import auth as gitlab_auth
from manage_users.api.gitlab import get_projects_and_members
from manage_users.api.grafana import auth as grafana_auth
from manage_users.api.grafana import create_user, create_team, add_user_to_team
from manage_users.models import User, Team

_LOG = logging.getLogger(__name__)


def retrieve_gitlab_data() -> Dict:
    URL = "https://gitlab.stud.idi.ntnu.no/"
    TOKEN = dotenv.get_key(".env", "GITLAB_ACCESS_TOKEN")
    gl = gitlab_auth(URL, TOKEN)

    # PARENT_GROUP_ID = 11911  # Mock project
    PARENT_GROUP_ID = 1042    # IT2810-H2018

    project_members = get_projects_and_members(gl, PARENT_GROUP_ID)
    print(project_members)
    return project_members


def main() -> None:
    projects_and_users = retrieve_gitlab_data()

    # Stores a mapping from (username,name) in gitlab to the grafana userid
    distinct_users = {}
    # iterate through all projects and add users to disctinct_users
    for ((_, _), users) in projects_and_users.items():
        for user in users:
            distinct_users[(user['username'], user['name'])] = None

    GRAFANA_API = grafana_auth(host='localhost:3000', username="admin", password="admin")

    # create a user for each distinct user and update distinct_user value with grafana user_id
    for username, name in distinct_users.keys():
        new_user = create_user(GRAFANA_API, User({
            "name": name,
            "email": f"{username}@blablabla.com",
            "password": "somepassword"
        }))
        distinct_users[(username, name)] = new_user['id']

    # stores a mapping from gitlab groups to the team_ids in Grafana
    teams = {}
    # create every project and add the correct users to the grafana team
    for ((group_id, group_name), users) in projects_and_users.items():
        new_team = create_team(GRAFANA_API, Team({"name": f"{group_name} [{group_id}]"}))
        teams[group_id] = new_team['teamId']
        for user in users:
            add_user_to_team(GRAFANA_API, distinct_users[(user['username'], user['name'])], new_team['teamId'])


if __name__ == "__main__":
    main()
