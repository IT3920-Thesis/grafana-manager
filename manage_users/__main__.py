import logging
from typing import Dict

import dotenv

from manage_users.api.gitlab import auth as gitlab_auth
from manage_users.api.gitlab import get_projects_and_members
from manage_users.api.grafana import auth as grafana_auth
from manage_users.api.grafana import create_user, create_team, add_user_to_team, create_folder, give_team_folder_read_rights
from manage_users.models import User, Team

_LOG = logging.getLogger(__name__)


def retrieve_gitlab_data(url, token, parent_group_id) -> Dict:
    gl = gitlab_auth(url, token)
    project_members = get_projects_and_members(gl, parent_group_id)
    return project_members


def generate_grafana_users(grafana_api, users: Dict[str, User]) -> Dict:
    generated_users = {}
    for username, user in users.items():
        new_user = create_user(grafana_api, User(**user))
        generated_users[username] = {**user, 'grafana_id': new_user['id']}
    return generated_users


def main() -> None:
    URL = "https://gitlab.stud.idi.ntnu.no/"
    TOKEN = dotenv.get_key("../.env", "GITLAB_ACCESS_TOKEN")
    # PARENT_GROUP_ID = 11911  # Mock project
    PARENT_GROUP_ID = 1042    # IT2810-H2018

    projects_and_users = retrieve_gitlab_data(URL, TOKEN, PARENT_GROUP_ID)

    # Stores a mapping from username in gitlab to the grafana userid
    distinct_users = {}

    # iterate through all projects and add users to disctinct_users
    # NTNU student mail inferred from gitlab username. When students have changed gitlab username it can cause problems
    for users in projects_and_users.values():
        for user in users:
            username = user['username']
            distinct_users[username] = User({
                'name': user['name'],
                'login': username,
                'password': 'somepassword',
                'email': f'{username}@stud.ntnu.no'
            })

    GRAFANA_API = grafana_auth(host='localhost:3000', username="admin", password="admin")

    # create a user for each distinct user and get mapping from username to the user_id in grafana
    grafana_users = generate_grafana_users(GRAFANA_API, distinct_users)

    teams = {}

    # create every team and folder with right privilegies. Then add the correct users to the grafana team
    for ((group_id, group_name), users) in projects_and_users.items():
        team_identifier = f"{group_name} [{group_id}]"
        new_team = create_team(GRAFANA_API, Team({"name": team_identifier}))
        new_folder = create_folder(GRAFANA_API, team_identifier)
        give_team_folder_read_rights(GRAFANA_API, new_folder['uid'], new_team['teamId'])
        team_members = []
        # Add all users to the team
        for user in users:
            username = user['username']
            user_id = grafana_users[username]['grafana_id']
            add_user_to_team(GRAFANA_API, user_id, new_team['teamId'])
            team_members.append({
                "username": username,
                "user_id": user_id
            })

        teams[team_identifier] = {
            "team_id": new_team['teamId'],
            "folder_uid": new_folder['uid'],
            "members": team_members
        }


if __name__ == "__main__":
    main()
