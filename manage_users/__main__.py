from manage_users.api import auth, create_user
from manage_users.mocks import get_mock_user
import logging

_LOG = logging.getLogger(__name__)


def main() -> None:
    GRAFANA_API = auth(host='localhost:3000', username="admin", password="admin")
    create_user(GRAFANA_API, get_mock_user())

if __name__ == "__main__":
    main()

