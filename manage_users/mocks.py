from manage_users.models import User, Team
from typing import List
from faker import Faker

fake = Faker('no_NO')


def get_mock_user() -> User:
    return User({"name": f"{fake.name()}", "email": f"{fake.email()}", "password": "password"})


def get_mock_team() -> Team:
    return Team({"name": f"{fake.company()}", "email": f"{fake.email()}"})


def get_n_mock_users(n) -> List[User]:
    return [get_mock_user() for _ in range(n)]


def get_n_mock_teams(n) -> List[Team]:
    return [get_mock_team() for _ in range(n)]
