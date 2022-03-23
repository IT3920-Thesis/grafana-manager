import logging
from typing import Dict

import dotenv
from grafana_api.grafana_face import GrafanaFace

from manage_users.api.gitlab import get_groups_and_members
from manage_users.api.grafana import auth as grafana_auth
from manage_users.api.grafana import create_user, create_team, add_user_to_team, create_folder, \
    give_team_folder_read_rights
from manage_users.models import User, Team

_LOG = logging.getLogger(__name__)


def retrieve_gitlab_data(gitlab_token, parent_group_id) -> Dict:
    return get_groups_and_members(gitlab_token, parent_group_id)


def generate_grafana_users(grafana_api: GrafanaFace, gitlab_groups_and_users) -> Dict:
    grafana_users = {}

    for group in gitlab_groups_and_users.values():
        for user in group['members']:
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


def generate_teams_and_assign_users(grafana_api: GrafanaFace, gitlab_groups_and_users, grafana_users) -> Dict:
    teams = {}
    for (group_name, group_dict) in gitlab_groups_and_users.items():
        new_team = create_team(grafana_api, Team({"name": group_name}))

        team_members = []
        # Add all users to the team
        for user in group_dict['members']:
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
            "gitlab_group": group_dict,
        }

    return teams


def main() -> None:
    TOKEN = dotenv.get_key("../.env", "GITLAB_ACCESS_TOKEN")
    PARENT_GROUP_ID = 11911  # Mock project
    # PARENT_GROUP_ID = 1042  # IT2810-H2018

    GRAFANA_API = grafana_auth(host='localhost:3000', username="admin", password="admin")

    # get all gitlab members from the sub groups of PARENT_GROUP_ID
    gitlab_groups_and_users = retrieve_gitlab_data(TOKEN, PARENT_GROUP_ID)
    # create a grafana user for all gitlab members
    grafana_users = generate_grafana_users(GRAFANA_API, gitlab_groups_and_users)
    # create a grafana team for each gitlab group and add the corresponding grafana users to the team
    grafana_teams = generate_teams_and_assign_users(GRAFANA_API, gitlab_groups_and_users, grafana_users)
    # create every team and folder with right privilegies. Then add the correct users to the grafana team
    grafana_teams = generate_folders_and_assign_privileges(GRAFANA_API, grafana_teams)


if __name__ == "__main__":
    main()
