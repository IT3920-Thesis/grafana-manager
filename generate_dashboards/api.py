import json

import requests
from grafanalib._gen import DashboardEncoder
from grafanalib.core import Dashboard
from typing import Optional


def get_dashboard_json(dashboard: Dashboard, folder_uid: Optional[str] = None):
    return json.dumps({
        "dashboard": dashboard.to_json_data(),
        "overwrite": True,
        "message": "test message",
        "folderUid": folder_uid
    }, indent=2, cls=DashboardEncoder)


def upload_to_grafana(json_dashboard, server, api_key, verify=True):
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    r = requests.post(f'http://{server}/api/dashboards/db', data=json_dashboard, headers=headers, verify=verify)
    r.raise_for_status()
    return r.json()
