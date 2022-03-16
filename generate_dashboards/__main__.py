import dotenv
from grafanalib.core import Dashboard, GridPos, SqlTarget
from custom_class import BarChart
from api import get_dashboard_json, upload_to_grafana, COMMIT_TYPE_CONTRIBUTIONS_SQL


def main():
    API_KEY = dotenv.get_key('../.env', "GRAFANA_API_KEY")
    SERVER = dotenv.get_key('../.env', "GRAFANA_SERVER")

    barchart_panel = BarChart(
        title="My first barchart",
        dataSource="default",
        targets=[
            SqlTarget(
                rawSql=COMMIT_TYPE_CONTRIBUTIONS_SQL,
                refId="A",
                format='table',
            ),
        ],
        gridPos=GridPos(h=8, w=24, x=0, y=0),
        editable=True
    )
    dashboard = Dashboard(
        title="My dashboard with barchart",
        panels=[barchart_panel],
        editable=True,
        schemaVersion=32
    )
    json_dashboard = get_dashboard_json(dashboard)
    upload_to_grafana(json_dashboard, SERVER, API_KEY, verify=True)


if __name__ == "__main__":
    main()
