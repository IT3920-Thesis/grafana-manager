import typing

from grafanalib.core import Dashboard, Time, Templating, GridPos, SqlTarget, TimeSeries, Threshold, Stat, RowPanel, \
    Table

from generate_dashboards.custom_class import BarChart

"""
This is the dashboard presenting an overview to each Student group
"""

# Minimum number of characters in a title before we consider it as large.
# The consensus are that around 50 characters are a good size
# https://gist.github.com/luismts/495d982e8c5b1a0ced4a57cf3d93cf60#write-good-commit-messages
_LONG_COMMIT_TITLE_THRESHOLD_CHARACTERS = 60


def long_commit_titles(gitlab_group_name: str, pos: typing.Optional[GridPos]) -> Stat:
    query = f'''
    SELECT
      $__timeGroup(commit_time, '1d') AS time,
      COUNT(commit_sha) as amount
    FROM
      commitaggregate
    WHERE
      group_id='{gitlab_group_name}' AND $__timeFilter(commit_time)
      AND (title ->> 'length')::numeric > {_LONG_COMMIT_TITLE_THRESHOLD_CHARACTERS}
      AND is_merge_commit=false
    GROUP BY time
    ORDER BY time ASC
    '''

    return Stat(
        title='Commits with long Titles',
        description='''Commits that have more than 60 characters are considered long.
        Merge commits are discarded.\n
        https://gist.github.com/luismts/495d982e8c5b1a0ced4a57cf3d93cf60#write-good-commit-messages
        ''',
        dataSource='default',
        colorMode='background',
        graphMode='area',
        gridPos=pos,
        targets=[
            SqlTarget(
                rawSql=query,
                refId='A',
                format='time_series',
            ),
        ],
    )


def large_commits(gitlab_group_name: str, pos: typing.Optional[GridPos]) -> Stat:
    query = f'''
    SELECT
      $__timeGroup(commit_time, '1d') AS time,
      COUNT(commit_sha) as amount
    FROM
      commitaggregate
    WHERE
      group_id='{gitlab_group_name}' AND $__timeFilter(commit_time)
      AND size='LARGE'
      AND is_merge_commit=false
    GROUP BY time
    ORDER BY time ASC
    '''

    panel = Stat(
        title='Large Commits',
        description='''
        This is determined by multiple factors. If only one file is changed,
        but contains a lot (> 800) of additions or deletions to the file,
        we consider it large. However, if a commit touches many files we also consider them large
        Merge commits are ignored.
        ''',
        dataSource='default',
        colorMode='background',
        graphMode='area',
        thresholdType='absolute',
        decimals=0,
        noValue='none',
        extraJson={
            # This didn't actually work
            'fieldConfig': {
                'default': {
                    'unit': 'short',
                },
            },
        },
        thresholds=[
            Threshold(
                index=0,
                color='#a5a5a5',
                value=0.0,
            ),
            Threshold(
                index=1,
                color='#EAB839',
                value=2.0,
            ),
            Threshold(
                index=2,
                color='red',
                value=10.0,
            ),
        ],
        gridPos=pos,
        targets=[
            SqlTarget(
                rawSql=query,
                refId='A',
                format='time_series',
            )
        ]
    )

    return panel


def commit_table(gitlab_group_name: str, pos: typing.Optional[GridPos]) -> Table:
    """
    Presents a timeline overview of the comits
    """
    query = f'''
    SELECT
      commit_time AS time,
      project_path as "Project",
      title->>'raw'::varchar as "Title",
      title->>'length' as "Title length",
      size,
      gitlab_issues_referenced as "Issues referenced"
    FROM
      commitaggregate
    WHERE
      group_id='{gitlab_group_name}' AND $__timeFilter(commit_time)
    ORDER BY time DESC
    '''

    panel = Table(
        title='Commits',
        description='',
        gridPos=pos,
        transparent=True,
        targets=[
            SqlTarget(
                rawSql=query,
                refId='A',
                format='time_series',
            ),
        ],
        overrides=[
            {
                "matcher": {"id": "byName", "options": "size"},
                "properties": [
                    {
                        "id": "custom.displayMode",
                        "value": "color-background-solid"
                    },
                    {
                        "id": "custom.width",
                        "value": 100
                    }
                ]
            },
            {
                "matcher": {"id": "byName", "options": "Issues referenced"},
                "properties": [
                    {
                        "id": "custom.displayMode",
                        "value": "json-view"
                    },
                    {
                        "id": "custom.width",
                        "value": 150
                    }
                ]
            },
            {
                "matcher": {"id": "byName", "options": "Time"},
                "properties": [
                    {
                        "id": "unit",
                        "value": "dateTimeAsIso"
                    },
                    {
                        "id": "custom.width",
                        "value": 150
                    }
                ]
            },
            {
                "matcher": {"id": "byName", "options": "Project"},
                "properties": [
                    {
                        "id": "custom.width",
                        "value": 200
                    }
                ]
            },
            {
                "matcher": {"id": "byName", "options": "Title"},
                "properties": [
                    {
                        "id": "custom.width",
                        "value": 350
                    },
                    {
                        "id": "unit",
                        "value": "string"
                    }
                ]
            },
            {
                "matcher": {"id": "byName", "options": "Title length"},
                "properties": [
                    {
                        "id": "custom.displayMode",
                        "value": "color-background-solid"
                    },
                    {
                        "id": "custom.width",
                        "value": 90
                    },
                    {
                        "id": "thresholds",
                        "value": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "orange", "value": None},
                                {"color": "transparent", "value": 10},
                                {"color": "orange", "value": 60}
                            ]
                        }
                    }
                ]
            }
        ],
    )

    return panel


def get_commits_per_commit_type_barchart(gitlab_group_name: str, pos: typing.Optional[GridPos]):
    COMMIT_PER_COMMIT_TYPE_SQL = f'''SELECT * FROM crosstab(
            $$
                SELECT author_email, type, count(DISTINCT commit_sha)
                FROM changecontribution
                WHERE group_id='{gitlab_group_name}' AND author_email IN (${'{filter_users}'})
                GROUP BY author_email, type
                ORDER BY author_email, type
            $$,
            $$
                SELECT type
                FROM (
                    VALUES ('CONFIGURATION'),
                    ('DOCUMENTATION'),
                    ('FUNCTIONAL'),
                    ('OTHER'),
                    ('TEST')) T(type)
            $$
            )
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
        gridPos=pos,
        editable=True,
    )


def get_accumulated_lines_added_time_series(gitlab_group_name: str, pos: typing.Optional[GridPos]) -> TimeSeries:
    return TimeSeries(
        title="Accumulated lines added per user",
        dataSource="default",
        spanNulls=True,
        targets=[
            SqlTarget(
                refId="B",
                format="time_series",
                rawSql=f"""
                SELECT
                  "timestamp" AS "time",
                  author_email,
                  SUM(lines_added) OVER
                    (PARTITION BY author_email ORDER BY "timestamp") AS "Accumulated lines added"
                FROM changecontribution
                WHERE $__timeFilter("timestamp")
                    AND group_id='{gitlab_group_name}'
                    AND author_email IN (${'{filter_users}'})
                    AND type IN (${'{commit_types}'})
                ORDER BY 1
        """
            )
        ],

        gridPos=pos,
        editable=True
    )


def get_accumulated_group_commits_time_series(gitlab_group_name: str, pos: typing.Optional[GridPos]) -> TimeSeries:
    return TimeSeries(
        title="Group commit timeline",
        dataSource="default",
        spanNulls=True,
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
                    WHERE group_id='{gitlab_group_name}' AND type IN (${'{commit_types}'})
                ) AS distinct_commits
                GROUP BY "time"
                """
            )
        ],
        gridPos=pos,
        editable=True
    )


def get_commit_size_bar_chart(gitlab_group_name: str, pos: typing.Optional[GridPos]) -> BarChart:
    return BarChart(
        title="Number of commits per commit size",
        dataSource="default",
        targets=[
            SqlTarget(
                rawSql=f"""
               SELECT * FROM crosstab(
    $$
        SELECT
            author_email,
            bucket,
            COUNT(bucket)
        FROM(
            SELECT
                author_email,
                (CASE
                    WHEN total_lines_added <= 50 THEN 'S'
                    WHEN total_lines_added <= 100 THEN 'M'
                    ELSE 'L'
                END) as bucket
                FROM (
                    SELECT author_email, SUM(lines_added) AS total_lines_added
                    FROM changecontribution
                    WHERE
                        group_id='{gitlab_group_name}' AND
                        author_email IN (${'{filter_users}'}) AND
                        type IN (${'{commit_types}'})
                    GROUP BY commit_sha,author_email
                    )AS distinct_commits
                ) AS buckets_per_commit
        GROUP BY author_email, bucket
        ORDER BY author_email, bucket
    $$,
    $$
        SELECT bucket
        FROM (VALUES ('S'), ('M'), ('L')) T(bucket)
    $$

    ) AS final_result(
        author_email varchar,
        "S (< 50)" bigint,
        "M (50-99)" bigint,
        "L (100<)" bigint
    )""",
                refId="D",
                format='table',
            ),
        ],
        gridPos=pos,
        editable=True,
    )


def group_overview(gitlab_group_name) -> Dashboard:
    panels = [
        RowPanel(title="Red flags", gridPos=GridPos(y=0, x=0, h=1, w=24)),
        long_commit_titles(gitlab_group_name, pos=GridPos(y=0, x=0, h=4, w=4)),
        large_commits(gitlab_group_name, pos=GridPos(y=0, x=4, h=4, w=4)),
        commit_table(gitlab_group_name, pos=GridPos(y=0, x=12, h=14, w=12)),
        RowPanel(title="Summary", gridPos=GridPos(y=1, x=0, h=1, w=24)),
        get_commits_per_commit_type_barchart(gitlab_group_name, pos=GridPos(y=1, x=0, h=8, w=24)),
        get_accumulated_lines_added_time_series(gitlab_group_name, pos=GridPos(y=8, x=0, h=8, w=12)),
        get_accumulated_group_commits_time_series(gitlab_group_name, pos=GridPos(y=8, x=12, h=8, w=12)),
        get_commit_size_bar_chart(gitlab_group_name, pos=GridPos(y=16, x=0, h=8, w=24)),
    ]

    for index, panel in enumerate(panels):
        panels[index].id = index

    dashboard = Dashboard(
        title=f"Main Dashboard [{gitlab_group_name}]",
        panels=panels,
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
            }, {
                "multi": True,
                "includeAll": True,
                "name": "commit_types",
                "label": "Commit Types",
                "description": "Choose which commit types to be included in the dashboard",
                "query": f"""
                        SELECT DISTINCT type
                        FROM changecontribution
                        WHERE group_id='{gitlab_group_name}'
                        """,
                "type": "query"
            }
            ])
    )

    return dashboard
