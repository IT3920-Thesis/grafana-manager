import unittest
from manage_users.api import create_team, auth, get_team_by_id, delete_team_by_id, \
    create_user, add_user_to_team, get_team_members_by_team_id, delete_user_by_id
from manage_users.mocks import get_mock_team, get_mock_user
from grafana_api.grafana_api import GrafanaException


class TeamCases(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TeamCases, self).__init__(*args, **kwargs)
        self.GRAFANA_API = auth(host='localhost:3000', username="admin", password="admin")

    def setUp(self) -> None:
        """
        Ran before every test function
        teardown_team_ids used to track new teams to be removed in tearDown.
        :return: None
        """
        self.MOCK_TEAM = get_mock_team()
        self.mock_team = create_team(self.GRAFANA_API, self.MOCK_TEAM)

        self.MOCK_USER = get_mock_user()
        self.mock_user_id = create_user(self.GRAFANA_API, self.MOCK_USER)['id']

        self.teardown_team_ids = [self.mock_team['teamId']]

    def tearDown(self) -> None:
        """
        Ran after every test function
        Deletes all the teams added to self.teardown_team_ids and the mock user
        :return:
        """
        for team_id in self.teardown_team_ids:
            delete_team_by_id(self.GRAFANA_API, team_id)
        delete_user_by_id(self.GRAFANA_API, self.mock_user_id)

    def test_create_team(self):
        new_team = create_team(self.GRAFANA_API, get_mock_team())
        self.assertEqual(new_team['message'], 'Team created')
        self.teardown_team_ids.append(new_team['teamId'])

    def test_delete_team(self):
        retrieved_mock_team = get_team_by_id(self.GRAFANA_API, self.mock_team['teamId'])
        self.assertEqual(retrieved_mock_team['id'], self.mock_team['teamId'], msg="A mocked team exists")

        delete_team_by_id(self.GRAFANA_API, self.mock_team['teamId'])
        # remove from teardown_team_ids as it is already deleted
        self.teardown_team_ids.remove(self.mock_team['teamId'])

        # test that team no longer is found in Grafana
        with self.assertRaises(GrafanaException, msg="A GrafanaException should be raised when retrieving "
                                                     "the deleted team"):
            get_team_by_id(self.GRAFANA_API, self.mock_team['teamId'])

    def test_create_duplicate_team_throws_exception(self) -> None:
        with self.assertRaises(GrafanaException, msg="Creating a team which "
                                                     "already exists should raise a GrafanaException"):
            create_team(self.GRAFANA_API, self.MOCK_TEAM)

    def test_add_user_to_team(self):
        team_members = get_team_members_by_team_id(self.GRAFANA_API, self.mock_team['teamId'])
        self.assertTrue(len(team_members) == 0, msg="There should not exist any members in the mocked team")
        response = add_user_to_team(self.GRAFANA_API, user_id=self.mock_user_id, team_id=self.mock_team['teamId'])
        self.assertEqual(response['message'], 'Member added to Team', msg="The response should confirm that a "
                                                                          "member has been added to the team")
        new_team_members = get_team_members_by_team_id(self.GRAFANA_API, self.mock_team['teamId'])
        self.assertTrue(len(new_team_members) == 1)
        self.assertTrue(new_team_members[0]['userId'] == self.mock_user_id)


if __name__ == '__main__':
    unittest.main()
