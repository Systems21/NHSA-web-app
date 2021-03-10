import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from layout_styles import CONTENT_STYLE, CARD_TEXT_STYLE
import dash_table
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
from app import app
import pathlib


content_second_row = dbc.Row(
    [
        dbc.Col(
            dcc.Graph(id='graph_2'), md=12
        )
    ]
)

content_second_textbox = dbc.Row([
    dbc.Col(
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.H4('Insight 3', className='card-title', style=CARD_TEXT_STYLE),
                        html.P('This chart shows us', style=CARD_TEXT_STYLE),
                    ]
                ),
            ], color='#f2d479'

        ),
        md=12
    )
])



def return_insights(fulldf):
    raceethnicity = fulldf
    countyname = fulldf.columns[1]
    raceethnicity = raceethnicity.drop(raceethnicity[(raceethnicity.Variable == "Total Population") | (raceethnicity.Variable == "Not Hispanic or Latino Total") | (raceethnicity.Variable == "Hispanic or Latino Total")].index)
    ethnicityvals = []
    racevals = []
    for var in raceethnicity["Variable"]:
        ethnicityvals.append(var.split('_')[0])
        racevals.append(var.split('_')[1])
    raceethnicity["Total Population"] = "Total Population"  # in order to have a single root node
    raceethnicity["Ethnicity"] = ethnicityvals
    raceethnicity["Race"] = racevals
    totalpop = sum(raceethnicity[countyname])
    raceethnicity["Percent of population"] = (raceethnicity[countyname] / totalpop) * 100
    percenteth = raceethnicity.groupby('Ethnicity').sum()
    percentnot = percenteth[percenteth.index=='Not Hispanic or Latino']['Percent of population'][0].round(2)
    percentyes = percenteth[percenteth.index=='Hispanic or Latino']['Percent of population'][0].round(2)

    fig1 = px.treemap(raceethnicity, path=['Total Population', 'Ethnicity', 'Race'], values=countyname,
                      color='Race')
    fig1.update_traces(marker_colors=["#00adf2",  # asian hispan
                                      "#fcce7e",  # some other not hispan
                                      "#00adf2",  # asian not hispan
                                      "lightblue",  # 2+ hispan
                                      "#cfa8ed",  # american indian not hispan
                                      "#fcce7e",  # some other hispan
                                      "pink",  # black hispan
                                      "lightblue",  # 2+ not hispan
                                      "pink",  # black not hispan
                                      "#a0e8b4",  # hispan white
                                      "magenta",  # hispan native hawaiian
                                      "#a0e8b4",  # white not hispan
                                      "#cfa8ed",  # american indian hispan
                                      "magenta",  # native hawaiian not hispan
                                      "darkblue",  # hispan total
                                      "blue",  # not hispan total
                                      "lightgray"])  # total population
    fig1.data[0].textinfo = 'label+text+value+percent parent'
    content_first_row = dbc.Row(
        [
            dbc.Col(
                dcc.Graph(id='graph_1', figure=fig1), md=12
            )
        ]
    )

    content_first_textbox = dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    [

                        dbc.CardBody(
                            [
                                html.H4(id='card_title_1', children=[countyname + ' Race and Ethnicity'], className='card-title',
                                        style=CARD_TEXT_STYLE),
                                html.P(id='card_text_1', children=[str(percentnot) + '% of residents do not identify as Hispanic or Latino, and ' + str(percentyes) + '% do identify as Hispanic or Latino'], style=CARD_TEXT_STYLE),
                            ]
                        )
                    ], color='#a9dad6'
                ),
                md=12
            )
        ]
    )

    return html.Div(
    [
        html.H3('Insights by Category'),
        html.H4('Race and Ethnicity'),
        content_first_row,
        content_first_textbox,
        content_second_row,
        content_second_textbox
    ],
    style=CONTENT_STYLE
)

