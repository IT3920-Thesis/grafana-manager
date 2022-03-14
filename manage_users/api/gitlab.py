from typing import List, Dict

import dotenv
from gitlab import Gitlab
from gitlab.v4.objects.projects import GroupProject

import logging

_LOG = logging.getLogger(__name__)


def auth(url: str, private_token: str) -> Gitlab:
    gl = Gitlab(url=url, private_token=private_token, per_page=100)
    gl.auth()
    _LOG.info("Gitlab instance authenticated")
    return gl


def get_projects_by_group_id(gl: Gitlab, group_id: int) -> List[GroupProject]:
    group = gl.groups.get(group_id, all=True)
    project_iterator = group.projects.list(as_list=False)
    return [project for project in project_iterator]


def get_members_by_project_id(gl: Gitlab, project_id: int) -> List:
    project = gl.projects.get(project_id, all=True)
    member_iterator = project.members.list(as_list=False)
    return [member for member in member_iterator]


def get_subgroup_ids_by_parent_group_id(gl, parent_group_id) -> List[int]:
    parent_group = gl.groups.get(parent_group_id)
    subgroup_iterator = parent_group.subgroups.list(as_list=False)
    return [subgroup.id for subgroup in subgroup_iterator]


def get_all_projects_by_parent_group_id(gl: Gitlab, parent_group_id):
    subgroup_ids = get_subgroup_ids_by_parent_group_id(gl, parent_group_id)

    projects = []
    for group_id in subgroup_ids:
        for project in get_projects_by_group_id(gl, group_id):
            projects.append(project)

    return projects


def get_projects_and_members(gl: Gitlab, parent_group_id: int) -> Dict:
    """
    Retrieves all projects and their members from subgroups underneath a specific parent group

    :param gl: an authenticated gitlab.Gitlab instance
    :param parent_group_id:
    :return: Dict of [project_id:int, project_name:str]=[{id:int, username:str, name:str}...]
    """
    project_members = {}

    # get all projects
    for project in get_all_projects_by_parent_group_id(gl, parent_group_id):
        # get all members in projects
        for member in get_members_by_project_id(gl, project.id):
            project_members[(project.id, project.name)] = [
                {"member_id": member.id, "username": member.username, "name": member.name}
            ]
    return project_members


# def main():
#     URL = "https://gitlab.stud.idi.ntnu.no/"
#     TOKEN = dotenv.get_key("../.env", "GITLAB_ACCESS_TOKEN")
#
#     PARENT_GROUP_ID = 11911     # Mock project
#     # PARENT_GROUP_ID = 1042    # IT2810-H2018
#
#     gl = auth(URL, TOKEN)
#     project_members = get_projects_and_members(gl, PARENT_GROUP_ID)
#
#     for item in project_members.items():
#         print(item)
#
#
# main()