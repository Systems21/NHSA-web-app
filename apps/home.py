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

# The structure of the home content is dependent on the variable categories the user selected from the sidebar,
# housed in the index file. Therefore, the content returned to index must be able to vary in both size and substance.

def return_insights(fulldf):
    countyname = fulldf.columns[1]
    if 'Race and Ethnicity' in set(fulldf.category):
        headerRE = html.H4('Race and Ethnicity')
        raceethnicity = fulldf[fulldf.category=='Race and Ethnicity']
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
        figRE = px.treemap(raceethnicity, path=['Total Population', 'Ethnicity', 'Race'], values=countyname,
                          color='Race')
        figRE.update_traces(marker_colors=["#00adf2",  # asian hispan
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
        figRE.data[0].textinfo = 'label+text+value+percent parent'
        content_RE_row = dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(figure=figRE), md=12
                )
            ]
        )
        content_RE_textbox = dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [

                            dbc.CardBody(
                                [
                                    html.H4(children=[countyname + ' Ethnicity'], className='card-title', style=CARD_TEXT_STYLE),
                                    html.P(children=[str(percentnot) + '% of residents do not identify as Hispanic or Latino, and ' + str(percentyes) + '% do identify as Hispanic or Latino'], style=CARD_TEXT_STYLE),
                                ]
                            )
                        ], color='#a9dad6'
                    ),
                    md=12
                )
            ]
        )
    else:
        headerRE = None
        content_RE_row = None
        content_RE_textbox = None
    if 'Children Under 6 Population Living With Family' in set(fulldf.category):
        headerC6 = html.H4('Child Population')
        livingwithtwo = fulldf[countyname][fulldf["Variable"][fulldf["Variable"] == 'Living with two parents'].index[0]]
        livingwithone = fulldf[countyname][fulldf["Variable"][fulldf["Variable"] == 'Living with one parent'].index[0]]
        df6 = pd.DataFrame(
            {"Variable": ['Both parents native', 'Both parents foreign born', 'One native and one foreign-born parent',
                          'Parent is native', 'Parent is foreign-born'],
             "Household Composition": ['Living with two parents', 'Living with two parents', 'Living with two parents',
                                       'Living with one parent', 'Living with one parent'],
             "Total children under 6": [fulldf[countyname][fulldf["Variable"][fulldf["Variable"] == 'Both parents native'].index[0]],
                                        fulldf[countyname][fulldf["Variable"][fulldf["Variable"] == 'Both parents foreign born'].index[0]],
                                        fulldf[countyname][fulldf["Variable"][fulldf["Variable"] == 'One native and one foreign-born parent'].index[0]],
                                        fulldf[countyname][fulldf["Variable"][fulldf["Variable"] == 'Parent is native'].index[0]],
                                        fulldf[countyname][fulldf["Variable"][fulldf["Variable"] == 'Parent is foreign-born'].index[0]]]})
        figC6 = px.bar(df6, x="Household Composition", y="Total children under 6", color="Variable")
        content_C6_row = dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(id='graph_2', figure=figC6), md=12
                )
            ]
        )
        content_C6_textbox = dbc.Row([
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H4(children=['Child Population in ' + countyname], className='card-title',
                                        style=CARD_TEXT_STYLE),
                                html.P(children=['There are ' + str(
                                    livingwithtwo) + ' children under 6 living with two parents and ' + str(
                                    livingwithone) + ' living with one parent in ' + countyname],
                                       style=CARD_TEXT_STYLE),
                            ]
                        ),
                    ], color='#f2d479'

                ),
                md=12
            )
        ])
    else:
        headerC6 = None
        content_C6_row = None
        content_C6_textbox = None

    possiblecontentlist = [headerRE,
                           content_RE_row,
                           content_RE_textbox,
                           headerC6,
                           content_C6_row,
                           content_C6_textbox]
    truecontentlist = []
    for element in possiblecontentlist:
        if element!=None:
            truecontentlist.append(element)

    return html.Div(truecontentlist, style=CONTENT_STYLE)

