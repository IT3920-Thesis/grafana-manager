import dataclasses
from typing import List, Union

from grafanalib.core import SqlTarget, TABLE_TARGET_FORMAT, TIME_SERIES_TARGET_FORMAT


def sql_query(raw_str: str) -> dict:
    return raw_str.strip()


class TimeSeriesSqlQuery(SqlTarget):
    def __init__(self, sql: str) -> None:
        super().__init__()
        self.rawSql = sql_query(sql)
        self.format = TIME_SERIES_TARGET_FORMAT


class TableSqlQuery(SqlTarget):
    def __init__(self, sql: str) -> None:
        super().__init__()
        self.rawSql = sql_query(sql)
        self.format = TABLE_TARGET_FORMAT


def rename_by_regex(regex: str, rename: str) -> dict:
    return {
        'id': 'renameByRegex',
        'options': {
            'regex': regex,
            'renamePattern': rename,
        },
    }


def sql_annotation(name: str, raw_query: str, color: str = 'purple') -> dict:
    return {
        'enable': True,
        'iconColor': color,
        'name': name,
        'rawQuery': raw_query.strip(),
    }


def annotate_with_milestones(group_id: str, color: str) -> dict:
    return sql_annotation(
        name='Milestones',
        color=color,
        raw_query=f'''
        select
            $__timeEpoch(created_at),
            CASE
                WHEN state = 'CLOSED' THEN extract(epoch from closed_at)
                -- Open issues have no close date  
                ELSE extract(epoch from now())
            END AS "timeend",
            title->>'raw' as "text",
            CONCAT('author:  ', author) AS "tags"
        from issueaggregate
        WHERE group_id = '{group_id}'
        ''',
    )


@dataclasses.dataclass(frozen=True)
class OverrideProperty:
    id: str
    value: Union[dict, str, int]


def override_by_name(name: str, properties: List[OverrideProperty]) -> dict:
    return {
        'matcher': {
            'id': 'byName',
            'options': name,
        },
        'properties': [
            {
                'id': prop.id,
                'value': prop.value,
            }
            for prop in properties
        ]
    }
