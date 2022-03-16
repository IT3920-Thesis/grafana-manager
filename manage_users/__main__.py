import logging
from typing import Dict

import dotenv
from grafana_api.grafana_face import GrafanaFace

from manage_users.api.gitlab import auth as gitlab_auth
from manage_users.api.gitlab import get_projects_and_members
from manage_users.api.grafana import auth as grafana_auth
from manage_users.api.grafana import create_user, create_team, add_user_to_team, create_folder, \
    give_team_folder_read_rights
from manage_users.models import User, Team

_LOG = logging.getLogger(__name__)


def retrieve_gitlab_data(url, token, parent_group_id) -> Dict:
    gl = gitlab_auth(url, token)
    return get_projects_and_members(gl, parent_group_id)


def generate_grafana_users(grafana_api: GrafanaFace, gitlab_projects_and_users) -> Dict:
    grafana_users = {}

    for users in gitlab_projects_and_users.values():
        for user in users:
            username = user['username']
            if username not in grafana_users.keys():
                new_user = User({
                    'name': user['name'],
                    'login': username,
                    'password': 'somepassword',
                    'email': f'{username}@stud.ntnu.no'
                })
                response = create_user(grafana_api, new_user)
                grafana_users[username] = {**new_user, 'grafana_id': response['id']}
    return grafana_users


def generate_folders_and_assign_privileges(grafana_api: GrafanaFace, grafana_teams):
    for group_name, team_dict in grafana_teams.items():
        new_folder = create_folder(grafana_api, group_name)
        give_team_folder_read_rights(grafana_api, new_folder['uid'], team_dict['team_id'])
        grafana_teams[group_name] = {**team_dict, "folder_uid": new_folder['uid']}
    return grafana_teams


def generate_teams_and_assign_users(grafana_api: GrafanaFace, gitlab_projects_and_users, grafana_users) -> Dict:
    teams = {}
    for ((group_id, group_name), users) in gitlab_projects_and_users.items():
        new_team = create_team(grafana_api, Team({"name": group_name}))

        team_members = []
        # Add all users to the team
        for user in users:
            username = user['username']
            user_id = grafana_users[username]['grafana_id']
            add_user_to_team(grafana_api, user_id, new_team['teamId'])
            team_members.append({
                "username": username,
                "user_id": user_id
            })
        teams[group_name] = {
            "team_id": new_team['teamId'],
            "members": team_members,
            "gitlab_group_id": group_id
        }

    return teams


def main() -> None:
    URL = "https://gitlab.stud.idi.ntnu.no/"
    TOKEN = dotenv.get_key("../.env", "GITLAB_ACCESS_TOKEN")
    PARENT_GROUP_ID = 11911  # Mock project
    # PARENT_GROUP_ID = 1042  # IT2810-H2018

    GRAFANA_API = grafana_auth(host='localhost:3000', username="admin", password="admin")

    # create a user for each distinct user and get mapping from username to the user_id in grafana
    gitlab_projects_and_users = retrieve_gitlab_data(URL, TOKEN, PARENT_GROUP_ID)
    grafana_users = generate_grafana_users(GRAFANA_API, gitlab_projects_and_users)

    grafana_teams = generate_teams_and_assign_users(GRAFANA_API, gitlab_projects_and_users, grafana_users)
    # # create every team and folder with right privilegies. Then add the correct users to the grafana team
    grafana_teams = generate_folders_and_assign_privileges(GRAFANA_API, grafana_teams)


if __name__ == "__main__":
    main()
