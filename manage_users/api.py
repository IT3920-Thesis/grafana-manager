from grafana_api.grafana_face import GrafanaFace
from class_types import User, Team
import logging


def make_member(grafana_api: GrafanaFace, user: User):
    user = grafana_api.admin.create_user(user)


def make_team(grafana_api: GrafanaFace, team: Team):
    response = grafana_api.teams.add_team(team)
    if response["message"] == "Team created":
        return response["teamId"]
    return -1


def add_member_to_team(grafana_api: GrafanaFace, user_id: str, team_id: int):
    return grafana_api.teams.add_team_member(team_id, user_id)


def get_team_members_by_team_id(grafana_api: GrafanaFace, team_id: int):
    return grafana_api.teams.get_team_members(team_id)
