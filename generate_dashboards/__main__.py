import dotenv
from grafanalib.core import Dashboard

from api import get_dashboard_json, upload_to_grafana


def main():
    API_KEY = dotenv.get_key('../.env', "GRAFANA_API_KEY")
    SERVER = dotenv.get_key('../.env', "GRAFANA_SERVER")

    dashboard = Dashboard(title="My awesome dashboard")
    json_dashboard = get_dashboard_json(dashboard)
    upload_to_grafana(json_dashboard, SERVER, API_KEY, verify=True)


if __name__ == "__main__":
    main()
