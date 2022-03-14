import unittest
from manage_users.api.grafana import auth, create_user, delete_user_by_id, get_user_by_id
from manage_users.mocks import get_mock_user
from grafana_api.grafana_api import GrafanaException

from manage_users.models import User


class UserCases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(UserCases, self).__init__(*args, **kwargs)
        self.GRAFANA_API = auth(host='localhost:3000', username="admin", password="admin")

    def setUp(self) -> None:
        """
        Ran before every test function
        Initiates auth in GRAFANA_API and a tracker of added users for tearDown()
        :return: None
        """
        self.MOCK_USER = get_mock_user()

        self.mock_user_id = create_user(self.GRAFANA_API, self.MOCK_USER)['id']
        self.teardown_user_ids = [self.mock_user_id]

    def tearDown(self) -> None:
        """
        Ran after every test function
        Deletes all the users added to self.teardown_user_ids
        :return:
        """
        for user_id in self.teardown_user_ids:
            delete_user_by_id(self.GRAFANA_API, user_id)

    def test_create_user(self) -> None:
        new_user = create_user(self.GRAFANA_API, get_mock_user())
        self.assertEqual(new_user['message'], 'User created')
        self.assertIsInstance(new_user['id'], int)
        # add id for tearDown
        self.teardown_user_ids.append(new_user['id'])

    def test_create_duplicate_user_throws_exception(self) -> None:
        print(self.teardown_user_ids)
        with self.assertRaises(ValueError):
            create_user(self.GRAFANA_API, self.MOCK_USER)

    def test_delete_user(self):
        retrieved_mock_user = get_user_by_id(self.GRAFANA_API, self.mock_user_id)
        self.assertEqual(retrieved_mock_user['id'], self.mock_user_id)
        delete_user_by_id(self.GRAFANA_API, self.mock_user_id)
        # remove from teardown_user_ids as it is already deleted
        self.teardown_user_ids.remove(self.mock_user_id)

        # test that user no longer is found in Grafana
        with self.assertRaises(GrafanaException):
            get_user_by_id(self.GRAFANA_API, self.mock_user_id)


if __name__ == '__main__':
    unittest.main()
