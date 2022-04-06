import typing

from grafanalib.core import Dashboard, Time, Templating, GridPos, SqlTarget, TimeSeries, Threshold, Stat, RowPanel, \
    Table, Annotations

from generate_dashboards.custom_class import BarChart
from generate_dashboards.dashboard.util import rename_by_regex, annotate_with_milestones, sql_query, override_by_name, \
    OverrideProperty, TimeSeriesSqlQuery, TableSqlQuery

"""
This is the dashboard presenting an overview to each Student group
"""

# Minimum number of characters in a title before we consider it as large.
# The consensus are that around 50 characters are a good size
# https://gist.github.com/luismts/495d982e8c5b1a0ced4a57cf3d93cf60#write-good-commit-messages
_LONG_COMMIT_TITLE_THRESHOLD_CHARACTERS = 60

CHANGE_TYPES = {
    'FUNCTIONAL': '#dbdbdb',
    'TEST': 'super-light-purple',
    'CONFIGURATION': 'super-light-green',
    'DOCUMENTATION': 'super-light-blue',
    'OTHER': 'red',
}


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
            Threshold(index=0, color='#a5a5a5', value=0.0),
            Threshold(index=1, color='#EAB839', value=2.0),
            Threshold(index=2, color='red', value=10.0),
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


def issues_without_description(gitlab_group_name: str, pos: typing.Optional[GridPos]) -> Stat:
    query = f'''
    SELECT
      $__timeGroup(created_at, '1d') as "time",
      COUNT(issue_iid) AS "value"
    FROM
      issueaggregate
    WHERE
      $__timeFilter(created_at) 
      AND (description->'length')::numeric < 1
      AND group_id = '{gitlab_group_name}'
    GROUP BY "time"
    '''

    panel = Stat(
        title='Issues without description',
        description='''
        Issues that lacks description can be difficult to understand by others
        '''.strip(),
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
            Threshold(index=0, color='super-light-green', value=0.0),
            Threshold(index=1, color='orange', value=1.0),
            Threshold(index=2, color='red', value=2.0),
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


def issues_with_short_titles(gitlab_group_name: str, pos: typing.Optional[GridPos]) -> Stat:
    query = f'''
    SELECT
      $__timeGroup(created_at, '1d') as "time",
      COUNT(issue_iid) AS "value"
    FROM
      issueaggregate
    WHERE
      $__timeFilter(created_at) 
      AND array_length(string_to_array(title->>'raw'::varchar, ' '), 1) < 3
      AND group_id = '{gitlab_group_name}'
    GROUP BY "time"
    '''.strip()

    panel = Stat(
        title='Issues with short titles',
        description='''
        Counts any title that have at most two words in it
        '''.strip(),
        dataSource='default',
        colorMode='background',
        graphMode='area',
        thresholdType='absolute',
        decimals=0,
        noValue='None',
        extraJson={
            # This didn't actually work
            'fieldConfig': {
                'default': {
                    'unit': 'short',
                },
            },
        },
        thresholds=[
            Threshold(index=0, color='super-light-green', value=0.0),
            Threshold(index=1, color='orange', value=1.0),
            Threshold(index=2, color='red', value=10.0),
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


def _duplicated_commit_titles(gitlab_group_name: str, pos: typing.Optional[GridPos]) -> Table:
    """
    Presents a timeline overview of the comits
    """
    query = TableSqlQuery(f'''
    SELECT
      title->'raw' as "Commit Title",
      project_path as "Project Path",
      COUNT(commit_sha) AS "duplicates"
    FROM
      commitaggregate
    WHERE
      $__timeFilter(commit_time) AND group_id = '{gitlab_group_name}'
    GROUP BY "Commit Title", "Project Path"
    HAVING COUNT(commit_sha) > 1
    ORDER BY duplicates desc
    ''')

    panel = Table(
        title='Duplicate commit titles',
        description='''
        Titles that are identical in name. Too many of these may indicate problematic
        commit practices.
        '''.strip(),
        gridPos=pos,
        transparent=False,
        targets=[query],
        thresholds=[
            Threshold(index=0, color='super-light-green', value=0.0),
            Threshold(index=1, color='orange', value=2.0),
            Threshold(index=2, color='red', value=4.0),
        ],
        overrides=[
            override_by_name('duplicates', [
                OverrideProperty(id='custom.displayMode', value='color-background'),
                OverrideProperty(id='custom.width', value=150),
            ]),
            override_by_name('Project Path', [
                OverrideProperty(id='custom.width', value=150),
            ]),
        ],
    )

    return panel


def _changes_by_type(gitlab_group_name: str, pos: typing.Optional[GridPos]) -> TimeSeries:
    label = 'value'
    query = TimeSeriesSqlQuery(f'''
    SELECT 
      $__timeGroup("timestamp", '1w') as "time",
      "type",
      COUNT(commit_sha) as "{label}"
    FROM changecontribution
    WHERE group_id = '{gitlab_group_name}'
    GROUP BY time, "type"
    ORDER BY time ASC
    ''')

    panel = TimeSeries(
        title='Changes by type',
        description='''
        '''.strip(),
        gridPos=pos,
        transparent=False,
        targets=[query],
        transformations=[rename_by_regex(label, '')],
        overrides=[
            override_by_name(name, [
                OverrideProperty(id='color', value={'fixedColor': color, 'mode': 'fixed'}),
            ])
            for name, color in CHANGE_TYPES.items()
        ],
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
            override_by_name('size', [
                OverrideProperty(id='custom.displayMode', value='color-background-solid'),
                OverrideProperty(id='custom.width', value=100),
            ]),
            override_by_name('Issues referenced', [
                OverrideProperty(id='custom.displayMode', value='json-view'),
                OverrideProperty(id='custom.width', value=150),
            ]),
            override_by_name('Time', [
                OverrideProperty(id='unit', value='dateTimeAsIso'),
                OverrideProperty(id='custom.width', value=150),
            ]),
            override_by_name('Project', [
                OverrideProperty(id='custom.width', value=200),
            ]),
            override_by_name('Title', [
                OverrideProperty(id='custom.width', value=350),
                OverrideProperty(id='unit', value='string'),
            ]),
            override_by_name('Title length', [
                OverrideProperty(id='custom.width', value=90),
                OverrideProperty(id='custom.displayMode', value='color-background-solid'),
                OverrideProperty(id='thresholds', value={
                    'mode': 'absolute',
                    'steps': [
                        {'color': 'orange', 'value': None},
                        {'color': 'transparent', 'value': 10},
                        {'color': 'orange', 'value': 60},
                    ],
                }),
            ]),
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


def accumulated_lines_contributed(gitlab_group_name: str, pos: typing.Optional[GridPos]) -> TimeSeries:
    label = 'Accumulated lines contributed'
    return TimeSeries(
        title="Accumulated lines contributed",
        dataSource="default",
        spanNulls=True,
        lineWidth=2,
        targets=[
            TimeSeriesSqlQuery(
                sql=f"""
                SELECT
                  "timestamp" AS "time",
                  author_email,
                  SUM(lines_added - lines_removed) OVER
                    (PARTITION BY author_email ORDER BY "timestamp") AS "{label}"
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
        editable=True,
        # We don't want to include the static label for each value
        # (more interested in author_email)
        transformations=[rename_by_regex(label, '')]
    )


def get_accumulated_group_commits_time_series(gitlab_group_name: str, pos: typing.Optional[GridPos]) -> TimeSeries:
    label = 'Commit count'
    return TimeSeries(
        title="Total Commits accumulated",
        description='Total number of commits accumulated by the student group',
        dataSource="default",
        spanNulls=True,
        lineWidth=2,
        overrides=[
            override_by_name(label, [
                OverrideProperty(id='color', value={'fixedColor': 'dark-blue', 'mode': 'fixed'}),
            ]),
        ],
        transformations=[rename_by_regex(label, '')],
        targets=[
            TimeSeriesSqlQuery(
                sql=sql_query(f"""
                SELECT
                    "time",
                    SUM(COUNT(commit_sha)) OVER (ORDER BY "time") AS "{label}"
                FROM (
                    SELECT
                        DISTINCT commit_sha,
                        "timestamp" AS "time"
                    FROM changecontribution
                    WHERE group_id='{gitlab_group_name}' AND type IN (${'{commit_types}'})
                ) AS distinct_commits
                GROUP BY "time"
                """)
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
            TableSqlQuery(
                sql=f"""
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
        _duplicated_commit_titles(gitlab_group_name, pos=GridPos(y=4, x=0, w=8, h=6)),

        issues_without_description(gitlab_group_name, pos=GridPos(y=0, x=12, h=4, w=4)),
        issues_with_short_titles(gitlab_group_name, pos=GridPos(y=0, x=16, h=4, w=4)),

        _changes_by_type(gitlab_group_name, pos=GridPos(y=0, x=12, w=10, h=8)),

        commit_table(gitlab_group_name, pos=GridPos(y=14, x=12, h=14, w=12)),

        RowPanel(title="Summary", gridPos=GridPos(y=20, x=0, h=1, w=24)),
        get_commits_per_commit_type_barchart(gitlab_group_name, pos=GridPos(y=1, x=0, h=8, w=24)),
        accumulated_lines_contributed(gitlab_group_name, pos=GridPos(y=8, x=0, h=8, w=12)),
        get_accumulated_group_commits_time_series(gitlab_group_name, pos=GridPos(y=8, x=12, h=8, w=12)),
        get_commit_size_bar_chart(gitlab_group_name, pos=GridPos(y=16, x=0, h=8, w=24)),
    ]

    for index, panel in enumerate(panels):
        panels[index].id = index

    dashboard = Dashboard(
        title=f"Overview",
        version=1000,
        panels=panels,
        editable=True,
        schemaVersion=32,
        time=Time(start="now-5y", end="now"),
        annotations=Annotations(
            list=[annotate_with_milestones(gitlab_group_name, color='super-light-purple')],
        ),
        templating=Templating(
            list=[{
                "multi": True,
                "includeAll": True,
                "name": "filter_users",
                "label": "Filter users",
                "description": "Choose which users to be included in the dashboard",
                "query": sql_query(f"""
                        SELECT DISTINCT author_email
                        FROM changecontribution
                        WHERE group_id='{gitlab_group_name}'
                        """),
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
                        """.strip(),
                "type": "query"
            }
            ])
    )

    return dashboard

# Time Taken on issue
#     {
#       "datasource": null,
#       "fieldConfig": {
#         "defaults": {
#           "color": {
#             "mode": "thresholds"
#           },
#           "custom": {
#             "axisLabel": "",
#             "axisPlacement": "auto",
#             "axisSoftMin": 1,
#             "fillOpacity": 99,
#             "gradientMode": "none",
#             "hideFrom": {
#               "legend": false,
#               "tooltip": false,
#               "viz": false
#             },
#             "lineWidth": 0
#           },
#           "decimals": 0,
#           "mappings": [],
#           "thresholds": {
#             "mode": "absolute",
#             "steps": [
#               {
#                 "color": "blue",
#                 "value": null
#               },
#               {
#                 "color": "#EAB839",
#                 "value": 1209600
#               },
#               {
#                 "color": "red",
#                 "value": 5184000
#               }
#             ]
#           },
#           "unit": "s"
#         },
#         "overrides": []
#       },
#       "gridPos": {
#         "h": 16,
#         "w": 17,
#         "x": 7,
#         "y": 16
#       },
#       "id": 10,
#       "options": {
#         "barWidth": 0.56,
#         "groupWidth": 0.7,
#         "legend": {
#           "calcs": [],
#           "displayMode": "hidden",
#           "placement": "bottom"
#         },
#         "orientation": "horizontal",
#         "showValue": "auto",
#         "stacking": "none",
#         "text": {},
#         "tooltip": {
#           "mode": "single"
#         }
#       },
#       "targets": [
#         {
#           "format": "table",
#           "group": [],
#           "metricColumn": "none",
#           "rawQuery": true,
#           "rawSql": "SELECT\n  $__timeGroup(created_at, '1d') as \"time\",\n  CONCAT('#', issue_iid, ' ', title->>'raw') as \"Issue\",\n  now() as \"closed_at\",\n  case\n    -- 14 days in seconds\n    when issue_iid < 12 then 1209600\n    else EXTRACT(EPOCH FROM (now() - created_at))\n  end as \"value\"\nFROM\n  issueaggregate\nWHERE\n  $__timeFilter(created_at)\n",
#           "refId": "A",
#           "select": [
#             [
#               {
#                 "params": [
#                   "value"
#                 ],
#                 "type": "column"
#               }
#             ]
#           ],
#           "timeColumn": "time",
#           "where": [
#             {
#               "name": "$__timeFilter",
#               "params": [],
#               "type": "macro"
#             }
#           ]
#         }
#       ],
#       "title": "Time spent on issue",
#       "transformations": [
#         {
#           "id": "convertFieldType",
#           "options": {
#             "conversions": [],
#             "fields": {}
#           }
#         },
#         {
#           "id": "renameByRegex",
#           "options": {
#             "regex": "value",
#             "renamePattern": "Time taken"
#           }
#         }
#       ],
#       "type": "barchart"
#     },
