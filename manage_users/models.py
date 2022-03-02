from typing import Dict, Optional


class User(Dict):
    name: str
    email: str
    password: str
    login: Optional[str] = None
    orgId: Optional[int] = None


class Team(Dict):
    name: str
    email: str
    orgId: Optional[int] = None
