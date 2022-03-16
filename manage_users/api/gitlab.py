import logging
from typing import List, Dict

from gitlab import Gitlab

_LOG = logging.getLogger(__name__)


def auth(url: str, private_token: str) -> Gitlab:
    gl = Gitlab(url=url, private_token=private_token, per_page=100)
    gl.auth()
    _LOG.info("Gitlab instance authenticated")
    return gl


def get_members_by_group_id(gl: Gitlab, group_id: int) -> List:
    return gl.groups.get(group_id).members.list()


def get_subgroups_from_parent_group_id(gl, parent_group_id) -> List[Dict]:
    parent_group = gl.groups.get(parent_group_id)
    subgroup_iterator = parent_group.subgroups.list(as_list=False)
    return [subgroup for subgroup in subgroup_iterator]


def get_groups_and_members(gl: Gitlab, parent_group_id: int) -> Dict:
    """
    Retrieves all subgroups and their members from a specific parent group
    :param gl: an authenticated gitlab.Gitlab instance
    :param parent_group_id: the id of the parent group
    :return: Dict({
        "group_id": int,
        "group_name": str,
        "parent_group_id": int,
        "members": [ Dict({ "member_id": int, "username": str, "name": str }), ... ]
    )}
    """
    groups = {}

    for group in get_subgroups_from_parent_group_id(gl, parent_group_id):
        members = []
        for member in get_members_by_group_id(gl, group.id):
            members.append({"member_id": member.id, "username": member.username, "name": member.name})
        group_dict = {
            "group_id": group.id,
            "group_name": group.name,
            "parent_group_id": group.parent_id,
            "members": members
        }
        groups[group.name] = group_dict
    return groups
