from grafanalib.core import Panel


class BarChart(Panel):
    """
    Overrides Panel.type to barchart.
    Can be further developed to support specific barchart features if needed, see bar chart docs[0].
    See implementation of Histogram(Panel)[1] for how it's done

    [0]: https://grafana.com/docs/grafana/latest/visualizations/bar-chart/
    [1]: https://github.com/weaveworks/grafanalib/blob/4a33bbb3b0a9dc069b7b343f4b83074969f92dc7/grafanalib/core.py
    """
    def to_json_data(self):
        barchart = self.panel_json(
            {
                'type': 'barchart',
            }
        )
        return barchart
