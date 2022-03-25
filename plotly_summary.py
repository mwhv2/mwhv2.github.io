    def summary(self):
        """
        Produces an interactive data summary in Jupyter notebook using the
        Plotly library. The plots here are identical to those created in
        the _repr_html_ method.

        Example
        -------
        >>> from sunpy.timeseries import TimeSeries
        >>> import sunpy.data.sample
        >>> goes_lc = TimeSeries(sunpy.data.sample.GOES_XRS_TIMESERIES)
        >>> goes_lc.summary()
        """
        try:
            from plotly.subplots import make_subplots
            import plotly.graph_objects as go
            import plotly.colors as colors
        except ModuleNotFoundError:
            print("Plotly library needed")

        # The components of _text_summary have to be redefined to be
        # passed into a Plotly table.
        obs = self.observatory
        if obs is None:
            try:
                obs = self.meta.metadata[0][2]["telescop"]
            except KeyError:
                obs = "Unknown"
        try:
            inst = self.meta.metadata[0][2]["instrume"]
        except KeyError:
            inst = "Unknown"
        try:
            link = f"""<a href="{self.url}" target="_blank">{inst} information</a>"""
        except AttributeError:
            link = None

        samp = self.shape[0]
        dat = self.to_dataframe()
        start = dat.index.min().round("s")
        end = dat.index.max().round("s")
        drange = dat.max() - dat.min()
        drange = drange.to_string(float_format="{:.2E}".format)
        drange = drange.replace("\n", "<br>")

        cha1 = self.meta.metadata[0][1]
        try:
            cha = self.channel_info
            cha = cha.replace("\n", "<br>")
        except AttributeError:
            cha = "<br>".join(cha1)

        uni = list(set(self.units.values()))
        uni = [x.unit if type(x) == u.quantity.Quantity else x for x in uni]
        uni = ["dimensionless" if x == u.dimensionless_unscaled else x for x in uni]
        uni = "<br>".join(str(x) for x in uni)

        # Define color list so each channel has matching colors in its
        # timeseries and histogram. The perm() function is necessary for
        # designating the visibility of plots using the dropdown menu.
        cols = colors.DEFAULT_PLOTLY_COLORS + colors.qualitative.Safe

        def perm(ind):
            P = [True, True] + [False for i in range(2 * len(cha1) - 2)]
            if ind == 0:
                return P
            else:
                Pnew = []
                for i in range(len(P)):
                    Pnew.append(P[i - 2 * ind])
                return Pnew

        # Initialize the plot, then create the timeseries and histograms.
        # Bin size is set to Scott's rule.
        fig = make_subplots(
            rows=2,
            cols=2,
            shared_xaxes=False,
            vertical_spacing=0.1,
            horizontal_spacing=0.12,
            specs=[
                [{"type": "table", "rowspan": 2}, {"type": "scatter"}],
                [None, {"type": "histogram"}],
            ],
        )
        for i in range(len(cha1)):
            fig.add_trace(
                go.Scatter(
                    x=dat.index,
                    y=dat[cha1[i]],
                    name=cha1[i],
                    marker=dict(color=cols[i]),
                ),
                row=1,
                col=2,
            )
            # Custom bin sizing slows down plotly's renderer a lot.
            # So, datasets with over 10 channels are set to use plotly's
            # default bin algorithm, which renders faster.
            if len(self.columns) < 10:
                binsize = astropy.stats.scott_bin_width(dat[cha1[i]].values)
            else:
                binsize = 0
            fig.add_trace(
                go.Histogram(
                    x=dat[cha1[i]].values,
                    name=cha1[i],
                    marker_color=cols[i],
                    xbins=dict(size=binsize),
                    showlegend=False,
                ),
                row=2,
                col=2,
            )
        Menu = [
            dict(
                label="All",
                method="update",
                args=[
                    {"visible": [True for j in range(len(cha1))]},
                    {
                        "yaxis.title": str(self.units[self.columns[0]]),
                        "xaxis2.title": str(self.units[self.columns[0]]),
                    },
                ],
            )
        ]
        for i in range(len(cha1)):
            Menu.append(
                dict(
                    label=cha1[i],
                    method="update",
                    args=[
                        {"visible": perm(i)},
                        {
                            "yaxis.title": str(self.units[self.columns[i]]),
                            "xaxis2.title": str(self.units[self.columns[i]]),
                        },
                    ],
                ),
            )
        fig.update_layout(
            updatemenus=[
                dict(
                    active=0,
                    showactive=True,
                    buttons=list(Menu),
                    x=0,
                    xanchor="left",
                    y=1.1,
                    yanchor="top",
                )
            ]
        )
        fig.add_trace(
            go.Table(
                cells=dict(
                    values=[
                        [
                            "<b>Observatory</b>",
                            "<b>Instrument</b>",
                            "<b>Channel(s)</b>",
                            "<b>Start Date</b>",
                            "<b>End Date</b>",
                            "<b>Samples per Channel</b>",
                            "<b>Data Range(s)</b>",
                            "<b>Units</b>",
                        ],
                        [obs, inst, cha, start, end, samp, drange, uni],
                    ],
                    align="right",
                )
            ),
            row=1,
            col=1,
        )
        fig["layout"]["yaxis2"]["title"] = "# of occurences"
        fig["layout"]["yaxis"]["tickformat"] = ".1e"
        fig["layout"]["xaxis2"]["tickformat"] = ".1e"

        fig.update_layout(height=700, hovermode="x", showlegend=False)
        fig.update_yaxes(type="log")
        if link is not None:
            fig.add_annotation(
                xref="paper", x="0", yref="paper", y="-0.1", text=link,
                showarrow=False
            )
        return fig.show()
