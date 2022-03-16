import dotenv
from grafanalib.core import Dashboard, GridPos, SqlTarget
from custom_class import BarChart
from api import get_dashboard_json, upload_to_grafana
from manage_users.api.grafana import get_all_folders, auth as grafana_auth


def get_commits_per_commit_type_barchart(gitlab_group_name):
    COMMIT_PER_COMMIT_TYPE_SQL = f'''SELECT * FROM crosstab(
            $$SELECT author_email, type, count(DISTINCT commit_sha)
            FROM changecontribution
            WHERE group_id='{gitlab_group_name}'
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


def get_folder_specific_json_dashboard(grafana_folder_uid, gitlab_group_name):
    dashboard = Dashboard(
        title="Grafana-manager dashboard",
        panels=[get_commits_per_commit_type_barchart(gitlab_group_name)],
        editable=True,
        schemaVersion=32,
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
    # print(all_folders)

    #
    # json_dashboard = get_folder_specific_json_dashboard(dashboard, grafana_folder_uid="HEPr4cEnk", gitlab_group_name=)
    # print(json_dashboard)
    # upload_to_grafana(json_dashboard, SERVER, API_KEY, verify=True)


if __name__ == "__main__":
    main()
