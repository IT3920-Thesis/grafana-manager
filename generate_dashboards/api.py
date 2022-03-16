import json

import requests
from grafanalib._gen import DashboardEncoder
from grafanalib.core import Dashboard

COMMIT_TYPE_CONTRIBUTIONS_SQL = '''SELECT * FROM crosstab(
        $$SELECT author_email, type, count(DISTINCT commit_sha)
        FROM changecontribution
        WHERE repository_id='randominternalproject002'
        GROUP BY author_email, type
        ORDER BY author_email, type $$)
    AS final_result(author_email varchar, CONFIGURATION bigint, DOCUMENTATION bigint, FUNCTIONAL bigint, OTHER bigint, TEST bigint)'''


def get_dashboard_json(dashboard:Dashboard):
    return json.dumps({
        "dashboard": dashboard.to_json_data(),
        "overwrite": True,
        "message": "test message"
    }, indent=2, cls=DashboardEncoder)


def upload_to_grafana(json_dashboard, server, api_key, verify=True):
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    print(json_dashboard)
    r = requests.post(f'http://{server}/api/dashboards/db', data=json_dashboard, headers=headers, verify=verify)
    r.raise_for_status()
    return r.json()