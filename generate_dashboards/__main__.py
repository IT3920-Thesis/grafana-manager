import dotenv
from grafanalib.core import Dashboard, GridPos, SqlTarget
from custom_class import BarChart
from api import get_dashboard_json, upload_to_grafana


def get_commits_per_commit_type_barchart():
    COMMIT_PER_COMMIT_TYPE_SQL = '''SELECT * FROM crosstab(
            $$SELECT author_email, type, count(DISTINCT commit_sha)
            FROM changecontribution
            WHERE repository_id='randominternalproject002'
            GROUP BY author_email, type
            ORDER BY author_email, type $$)
        AS final_result(
            author_email varchar,
            CONFIGURATION bigint,
            DOCUMENTATION bigint,
            FUNCTIONAL bigint,
            OTHER bigint,
            TEST bigint)'''

    return BarChart(
        title="Number of commits per contribution type",
        dataSource="default",
        targets=[
            SqlTarget(
                rawSql=COMMIT_PER_COMMIT_TYPE_SQL,
                refId="A",
                format='table',
            ),
        ],
        gridPos=GridPos(h=8, w=24, x=0, y=0),
        editable=True
    )


def main():
    API_KEY = dotenv.get_key('../.env', "GRAFANA_API_KEY")
    SERVER = dotenv.get_key('../.env', "GRAFANA_SERVER")

    dashboard = Dashboard(
        title="Grafana-manager dashboard",
        panels=[get_commits_per_commit_type_barchart()],
        editable=True,
        schemaVersion=32
    )
    json_dashboard = get_dashboard_json(dashboard)
    upload_to_grafana(json_dashboard, SERVER, API_KEY, verify=True)


if __name__ == "__main__":
    main()
