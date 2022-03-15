import itertools
import logging
from typing import Dict, List, Set

from grafana_api.grafana_api import GrafanaException
from grafana_api.grafana_face import GrafanaFace

from manage_users.models import User, Team

_LOG = logging.getLogger(__name__)
cached_user_emails = set()


def auth(host: str, username: str, password: str) -> GrafanaFace:
    _LOG.info(f'User {username} initiated auth to {host}')
    return GrafanaFace(auth=(username, password), host=host)


def get_all_cached_users(grafana_api: GrafanaFace) -> Set:
    global cached_user_emails
    if len(cached_user_emails) == 0:
        cached_user_emails = {user["email"] for user in get_all_users(grafana_api)}
    return cached_user_emails


def create_user(grafana_api: GrafanaFace, user: User) -> Dict:
    try:
        user_emails = get_all_cached_users(grafana_api)
        if user["email"] not in user_emails:
            new_user = grafana_api.admin.create_user(user)
            cached_user_emails.add(user["email"])
        else:
            _LOG.exception("Failed to create new user. Email already in use")
            raise ValueError("Failed to create new user. Email already in use")

    except GrafanaException as ge:
        _LOG.exception("Create user failed")
        raise ge
    return new_user


def get_all_users(grafana_api: GrafanaFace) -> List[Dict]:
    per_page = 1000
    users = []
    for n in itertools.count(start=1):
        resp = grafana_api.users.search_users(query=None, perpage=per_page, page=n)
        if len(resp) == 0:
            break
        users.extend(resp)
    return users


def delete_user_by_id(grafana_api: GrafanaFace, user_id: int):
    try:
        grafana_api.admin.delete_user(user_id)
        _LOG.info(f'User {user_id} deleted')
    except GrafanaException as ge:
        _LOG.exception("Delete user failed")
        raise ge


def delete_team_by_id(grafana_api: GrafanaFace, team_id: int):
    try:
        grafana_api.teams.delete_team(team_id)
        _LOG.info(f'Team {team_id} deleted')
    except GrafanaException as ge:
        _LOG.exception("Delete team failed")
        raise ge


def create_team(grafana_api: GrafanaFace, team: Team) -> Dict:
    response = grafana_api.teams.add_team(team)
    if response["message"] == "Team created":
        _LOG.info(f"Created the team: {team['name']} with team_id: {response['teamId']}")
        return response
    _LOG.error("Team creation failed", extra=response)
    raise GrafanaException(999, response, "Team creation failed for some unknown reason")


def get_all_teams(grafana_api: GrafanaFace) -> List[Dict]:
    per_page = 1000
    teams = []
    for n in itertools.count(start=1):
        resp = grafana_api.teams.search_teams(query=None, perpage=per_page, page=n)
        if len(resp) == 0:
            break
        teams.extend(resp)
    return teams


def get_team_by_id(grafana_api: GrafanaFace, team_id: int):
    try:
        response = grafana_api.teams.get_team(team_id)
        _LOG.info(f"Team {team_id} retrieved from ID")
    except GrafanaException as ge:
        _LOG.exception(f"Failed to get team {team_id} by id")
        raise ge
    return response


def add_user_to_team(grafana_api: GrafanaFace, user_id: int, team_id: int):
    response = grafana_api.teams.add_team_member(team_id, user_id)
    if response["message"] == "Member added to Team":
        _LOG.info(f"Added user: {user_id} to team {team_id}")
        return response
    _LOG.error("Adding user failed", extra=response)
    raise GrafanaException(999, response, "User was not added to team")


def get_team_members_by_team_id(grafana_api: GrafanaFace, team_id: int):
    try:
        response = grafana_api.teams.get_team_members(team_id)
        _LOG.info(f"Team members from team {team_id} retrieved from team_id")
    except GrafanaException as ge:
        _LOG.exception(f"Failed to get team members from team {team_id} by team_id")
        raise ge
    return response


def get_user_by_id(grafana_api: GrafanaFace, user_id: int):
    try:
        response = grafana_api.users.get_user(user_id)
        _LOG.info(f"User {user_id} retrieved from user_id")
    except GrafanaException as ge:
        _LOG.exception(f"Failed to get user {user_id} by user_id")
        raise ge
    return response


def delete_all_non_admin_users(grafana_api: GrafanaFace) -> None:
    _LOG.warning("Initiated deletion of all non-admin users")
    users = get_all_users(grafana_api)
    for user in users:
        if user["isAdmin"] is False:
            delete_user_by_id(grafana_api, user['id'])
        _LOG.info(f"Deleted user: {user['id']}")


def delete_all_teams(grafana_api: GrafanaFace):
    _LOG.warning("Initiated deletion of all teams")
    teams = get_all_teams(grafana_api)
    for team in teams:
        delete_team_by_id(grafana_api, team["id"])
        _LOG.info(f"Deleted team: {team['id']}")


# GRAFANA_API = auth(host='localhost:3000', username="admin", password="admin")
# delete_all_non_admin_users(GRAFANA_API)
# delete_all_teams(GRAFANA_API)