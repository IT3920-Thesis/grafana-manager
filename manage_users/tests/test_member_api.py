import unittest
from manage_users.api import auth, create_member, delete_member_by_id, get_member_by_id
from manage_users.mocks import get_mock_user
from grafana_api.grafana_api import GrafanaException


class MemberCases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(MemberCases, self).__init__(*args, **kwargs)
        self.GRAFANA_API = auth(host='localhost:3000', username="admin", password="admin")

    def setUp(self) -> None:
        """
        Ran before every test function
        Initiates auth in GRAFANA_API and a tracker of added members for tearDown()
        :return: None
        """
        self.MOCK_USER = get_mock_user()

        self.mock_member = create_member(self.GRAFANA_API, self.MOCK_USER)
        self.teardown_member_ids = [self.mock_member['id']]

    def tearDown(self) -> None:
        """
        Ran after every test function
        Deletes all the members added to self.teardown_member_ids
        :return:
        """
        for member_id in self.teardown_member_ids:
            delete_member_by_id(self.GRAFANA_API, member_id)

    def test_create_member(self) -> None:
        new_member = create_member(self.GRAFANA_API, get_mock_user())
        self.assertEqual(new_member['message'], 'User created')
        self.assertIsInstance(new_member['id'], int)
        # add id for tearDown
        self.teardown_member_ids.append(new_member['id'])

    def test_create_duplicate_member_throws_exception(self) -> None:
        with self.assertRaises(GrafanaException):
            create_member(self.GRAFANA_API, self.MOCK_USER)

    def test_delete_member(self):
        retrieved_mock_member = get_member_by_id(self.GRAFANA_API, self.mock_member['id'])
        self.assertEqual(retrieved_mock_member['id'], self.mock_member['id'])
        delete_member_by_id(self.GRAFANA_API, self.mock_member['id'])
        # remove from teardown_member_ids as it is already deleted
        self.teardown_member_ids.remove(self.mock_member['id'])

        # test that member no longer is found in Grafana
        with self.assertRaises(GrafanaException):
            get_member_by_id(self.GRAFANA_API, self.mock_member['id'])


if __name__ == '__main__':
    unittest.main()
