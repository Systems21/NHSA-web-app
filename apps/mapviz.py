import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import pathlib
from census import CensusViewer
from layout_styles import CONTENT_STYLE
from app import app

df = px.data.election()
geojson = px.data.election_geojson()
# configure data
# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("..").resolve()
# Create dataframe for simple selections and filters
state_county_choices = pd.read_csv(DATA_PATH.joinpath("state_county_fips.csv"))



content_first_row = dbc.Row(
    [
        dbc.Col(
            dcc.Graph(id='bigmap', figure=px.choropleth(locations=["CA", "TX", "NY"],
                                                        locationmode="USA-states",
                                                        color=[1,2,3],
                                                        scope="usa",
                                                        width=600).update_layout(margin={"r":0,"t":10,"l":0,"b":0})
                      )
        )
    ]
)



content = html.Div(
    [html.H2(' '),
     content_first_row],
    style=CONTENT_STYLE
)

layout = html.Div([content])
