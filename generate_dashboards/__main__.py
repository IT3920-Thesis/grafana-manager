import dotenv
from grafanalib.core import Dashboard, GridPos, SqlTarget, TimeSeries, Templating, Time

from api import get_dashboard_json, upload_to_grafana
from custom_class import BarChart
from manage_users.api.grafana import get_all_folders, auth as grafana_auth


def get_commits_per_commit_type_barchart(gitlab_group_name: str, panel_id: int):
    COMMIT_PER_COMMIT_TYPE_SQL = f'''SELECT * FROM crosstab(
            $$SELECT author_email, type, count(DISTINCT commit_sha)
            FROM changecontribution
            WHERE group_id='{gitlab_group_name}' AND author_email IN (${'{filter_users}'})
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
        id=panel_id,
        targets=[
            SqlTarget(
                rawSql=COMMIT_PER_COMMIT_TYPE_SQL,
                refId="A",
                format='table',
            ),
        ],
        gridPos=GridPos(h=8, w=24, x=0, y=0),
        editable=True,
    )


def get_accumulated_lines_added_time_series(gitlab_group_name: str, panel_id: int) -> TimeSeries:
    return TimeSeries(
        title="Accumulated lines added per user",
        dataSource="default",
        spanNulls=True,
        id=panel_id,
        targets=[
            SqlTarget(
                refId="B",
                format="time_series",
                rawSql=f"""
                SELECT
                  "timestamp" AS "time",
                  author_email,
                  SUM(lines_added - lines_removed) OVER
                    (PARTITION BY author_email ORDER BY "timestamp") AS "Accumulated lines added"
                FROM changecontribution
                WHERE type='FUNCTIONAL'
                    AND $__timeFilter("timestamp")
                    AND group_id='{gitlab_group_name}'
                    AND author_email IN (${'{filter_users}'})
                ORDER BY 1
        """
            )
        ],

        gridPos=GridPos(h=8, w=12, x=0, y=8),
        editable=True
    )


def get_accumulated_group_commits_time_series(gitlab_group_name:str, panel_id:int):
    return TimeSeries(
        title="Group commit timeline",
        dataSource="default",
        spanNulls=True,
        id=panel_id,
        targets=[
            SqlTarget(
                refId="D",
                format="time_series",
                rawSql=f"""
                SELECT
                    "time",
                    SUM(COUNT(commit_sha)) OVER (ORDER BY "time") AS "Commit count"
                FROM (
                    SELECT
                        DISTINCT commit_sha,
                        "timestamp" AS "time"
                    FROM changecontribution
                    WHERE type='FUNCTIONAL' AND group_id='{gitlab_group_name}'
                ) AS distinct_commits
                GROUP BY "time"
                """
            )
        ],
        gridPos=GridPos(h=8, w=12, x=12, y=8),
        editable=True
    )


def get_folder_specific_json_dashboard(grafana_folder_uid, gitlab_group_name):
    dashboard = Dashboard(
        title=f"Main Dashboard [{gitlab_group_name}]",
        panels=[
            get_commits_per_commit_type_barchart(gitlab_group_name, 1),
            get_accumulated_lines_added_time_series(gitlab_group_name, 2),
            get_accumulated_group_commits_time_series(gitlab_group_name, 3)
        ],
        editable=True,
        schemaVersion=32,
        time=Time(start="now-1y", end="now"),
        templating=Templating(
            list=[{
                    "multi": True,
                    "includeAll": True,
                    "name": "filter_users",
                    "label": "Filter users",
                    "description": "Choose which users to be included in the dashboard",
                    "query": f"""
                        SELECT DISTINCT author_email
                        FROM changecontribution
                        WHERE group_id='{gitlab_group_name}'
                        """,
                    "type": "query"
                }
            ])
    )
    json_dashboard = get_dashboard_json(dashboard, folder_uid=grafana_folder_uid)
    return json_dashboard


def main():
    API_KEY = dotenv.get_key('../.env', "GRAFANA_API_KEY")
    SERVER = dotenv.get_key('../.env', "GRAFANA_SERVER")

    GRAFANA_API = grafana_auth(host='localhost:3000', username="admin", password="admin")
    all_folders = get_all_folders(GRAFANA_API)

    for folder in all_folders:
        json_dashboard = get_folder_specific_json_dashboard(folder['uid'], folder['title'])
        upload_to_grafana(json_dashboard, SERVER, API_KEY, verify=True)


if __name__ == "__main__":
    main()
