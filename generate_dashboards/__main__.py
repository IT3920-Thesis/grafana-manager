import dotenv

from api import upload_to_grafana, get_dashboard_json
from generate_dashboards.dashboard.group_overview import group_overview
from manage_users.api.grafana import get_all_folders, auth as grafana_auth


def main():
    API_KEY = dotenv.get_key('../.env', "GRAFANA_API_KEY")
    SERVER = dotenv.get_key('../.env', "GRAFANA_SERVER")

    GRAFANA_API = grafana_auth(host='localhost:3000', username="admin", password="admin")
    all_folders = get_all_folders(GRAFANA_API)

    for folder in all_folders:
        overview = get_dashboard_json(group_overview(folder['title']), folder_uid=folder['uid'])
        upload_to_grafana(overview, SERVER, API_KEY, verify=True)


if __name__ == "__main__":
    main()
