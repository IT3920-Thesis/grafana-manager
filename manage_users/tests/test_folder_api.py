import unittest

from manage_users.api.grafana import auth, create_folder, delete_folder_by_uid, \
    get_all_folders


class FolderCases(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(FolderCases, self).__init__(*args, **kwargs)
        self.GRAFANA_API = auth(host='localhost:3000', username="admin", password="admin")

    def setUp(self) -> None:
        """
        Ran before every test function
        teardown_team_ids used to track new teams to be removed in tearDown.
        :return: None
        """
        self.mock_folder = create_folder(self.GRAFANA_API, "Mock Folder")

    def tearDown(self) -> None:
        """
        Ran after every test function
        Deletes all the teams added to self.teardown_team_ids and the mock user
        :return:
        """
        delete_folder_by_uid(self.GRAFANA_API, self.mock_folder['uid'])

    def test_create_folder(self):
        new_folder = create_folder(self.GRAFANA_API, 'test_create_folder folder')
        found_folder = False
        for folder in get_all_folders(self.GRAFANA_API):
            if folder['uid'] == new_folder['uid']:
                found_folder = True
        self.assertTrue(found_folder, msg="Folder should be found by get_all_folders after creation")

    def test_delete_folder(self):
        new_folder = create_folder(self.GRAFANA_API, "test_delete_folder folder")
        delete_folder_by_uid(self.GRAFANA_API, new_folder['uid'])
        all_folders = get_all_folders(self.GRAFANA_API)
        found_folder = False
        for folder in all_folders:
            if folder['uid'] == new_folder['uid']:
                found_folder = True
        self.assertFalse(found_folder, "Should not find folder with get_all_folders after deletion")


if __name__ == '__main__':
    unittest.main()
