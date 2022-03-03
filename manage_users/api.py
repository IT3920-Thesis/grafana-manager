from grafana_api.grafana_face import GrafanaFace
from grafana_api.grafana_api import GrafanaException
from manage_users.models import User, Team
from typing import Dict
import logging

_LOG = logging.getLogger(__name__)


def auth(host: str, username: str, password: str) -> GrafanaFace:
    _LOG.info(f'User {username} initiated auth to {host}')
    return GrafanaFace(auth=(username, password), host=host)


def create_member(grafana_api: GrafanaFace, user: User) -> Dict:
    try:
        member = grafana_api.admin.create_user(user)
    except GrafanaException as ge:
        _LOG.exception("Create member failed")
        raise ge
    return member


def delete_member_by_id(grafana_api: GrafanaFace, user_id: int):
    grafana_api.admin.delete_user(user_id)


def delete_team_by_id(grafana_api: GrafanaFace, team_id: int):
    grafana_api.teams.delete_team(team_id)


def create_team(grafana_api: GrafanaFace, team: Team) -> Dict:
    response = grafana_api.teams.add_team(team)
    if response["message"] == "Team created":
        _LOG.info(f"Created the team: {team['name']} with team_id: {response['teamId']}")
        return response
    _LOG.error("Team creation failed", extra=response)
    raise GrafanaException(999, response, "Team creation failed for some unknown reason")


def get_team_by_id(grafana_api: GrafanaFace, team_id: int):
    return grafana_api.teams.get_team(team_id)


def add_member_to_team(grafana_api: GrafanaFace, user_id: str, team_id: int):
    _LOG.info(f"Added member: {user_id} to team {team_id}")
    return grafana_api.teams.add_team_member(team_id, user_id)


def get_team_members_by_team_id(grafana_api: GrafanaFace, team_id: int):
    return grafana_api.teams.get_team_members(team_id)


def get_member_by_id(grafana_api: GrafanaFace, user_id: int):
    return grafana_api.users.get_user(user_id)
