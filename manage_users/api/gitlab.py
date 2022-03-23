import logging
from typing import List, Dict

import requests

_LOG = logging.getLogger(__name__)


def get_members_by_group_id(gitlab_token, group_id) -> List:
    r = requests.get(
        f"https://gitlab.stud.idi.ntnu.no/api/v4/groups/{group_id}/members/all",
        verify=False,
        headers={
            "PRIVATE-TOKEN": gitlab_token},
    )
    return r.json()


def get_subgroups_from_parent_group_id(gitlab_token, parent_group_id) -> List:
    r = requests.get(
        f"https://gitlab.stud.idi.ntnu.no/api/v4/groups/{parent_group_id}/subgroups",
        verify=False,
        headers={
            "PRIVATE-TOKEN": gitlab_token
        }
    )
    return r.json()


def get_groups_and_members(gitlab_token, parent_group_id: int) -> Dict:
    """
    Retrieves all subgroups and their members from a specific parent group
    :param gitlab_token: a gitlab access token
    :param parent_group_id: the id of the parent group
    :return: Dict({
        "group_id": int,
        "group_name": str,
        "parent_group_id": int,
        "members": [ Dict({ "member_id": int, "username": str, "name": str }), ... ]
    )}
    """
    groups = {}

    for group in get_subgroups_from_parent_group_id(gitlab_token, parent_group_id):
        members = []
        for member in get_members_by_group_id(gitlab_token, group['id']):
            members.append({"member_id": member['id'], "username": member['username'], "name": member['name']})
        group_dict = {
            "group_id": group['id'],
            "group_name": group['name'],
            "parent_group_id": group['parent_id'],
            "members": members
        }
        groups[group['name']] = group_dict
    return groups
