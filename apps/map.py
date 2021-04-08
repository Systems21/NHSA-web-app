import geojson
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from census import CensusViewer
from layout_styles import CONTENT_STYLE, CARD_TEXT_STYLE
from app import app
from urllib.request import urlopen



def return_maps(svars, scounties, sstates, state_county_choices, vardf):
    if svars[0] in ['Total population', 'Teen mothers', 'Child Poverty','SSI, Cash Public Assistance, Food Stamps', 'Health Insurance Coverage', 'School Enrollment']:
        present, past, state_fip, county_fips = CensusViewer(api_key='e12de88e1f23dcdd9a802fbbb92b362a1e67c3c4').build_mapping_df([scounties], sstates, svars)
        cnty = state_county_choices[state_county_choices['County'] == scounties]
        countytracts = []
        stateurl = 'https://raw.githubusercontent.com/Systems21/NHSA-web-app/main/assets/tracts_' + sstates + '.geojson'
        with urlopen(stateurl) as response:
            tractgeos = geojson.load(response)
        for poly in tractgeos["features"]:
            if poly["properties"]["COUNTYFP"] == county_fips[0]:
                countytracts.append(poly)
        countytractgeos = geojson.FeatureCollection(countytracts)
        lon = float(cnty['centerlat'].iloc[0])
        lat = float(cnty['centerlon'].iloc[0])
        if svars[0] in ['Total population', 'Teen mothers', 'Unemployment Rate',
                        'Unemployment, Households with Children under 6', 'Household Composition (children under 6)']:
            totalpop = present.columns[0]
            lab = vardf[vardf['vars'] == totalpop].name.iloc[0]
            fig = px.choropleth_mapbox(present, geojson=countytractgeos, locations='TRACTCE',
                                       featureidkey="properties.TRACTCE",
                                       color=totalpop,
                                       color_continuous_scale="orrd",
                                       range_color=(0, max(present[totalpop])),
                                       mapbox_style="carto-positron",
                                       zoom=7, center={"lat": lat, "lon": lon},
                                       opacity=0.7,
                                       labels={totalpop: lab}
                                       ).update_layout(margin={"r": 0, "t": 10, "l": 0, "b": 0})
        elif svars[0] in ['SSI, Cash Public Assistance, Food Stamps', 'Health Insurance Coverage']:
            universe = present.columns[0]
            prop = present.columns[1]
            lab = 'Percent ' + vardf[vardf['vars'] == prop].name.iloc[0]
            present[lab] = (present[prop] / present[universe]) * 100
            fig = px.choropleth_mapbox(present, geojson=countytractgeos, locations='TRACTCE',
                                       featureidkey="properties.TRACTCE",
                                       color=lab,
                                       color_continuous_scale="orrd",
                                       range_color=(0, max(present[lab])),
                                       mapbox_style="carto-positron",
                                       zoom=7, center={"lat": lat, "lon": lon},
                                       opacity=0.7,
                                       ).update_layout(margin={"r": 0, "t": 10, "l": 0, "b": 0})
        elif svars[0] == 'Child Poverty':
            present["Population 5 and under living below poverty"] = present['B17001_004E'] + present['B17001_005E'] + \
                                                                     present['B17001_018E'] + present['B17001_019E']
            fig = px.choropleth_mapbox(present, geojson=countytractgeos, locations='TRACTCE',
                                       featureidkey="properties.TRACTCE",
                                       color="Population 5 and under living below poverty",
                                       color_continuous_scale="orrd",
                                       range_color=(0, max(present["Population 5 and under living below poverty"])),
                                       mapbox_style="carto-positron",
                                       zoom=7, center={"lat": lat, "lon": lon},
                                       opacity=0.7,
                                       width=600
                                       ).update_layout(margin={"r": 0, "t": 10, "l": 0, "b": 0})
        elif svars[0] == 'School Enrollment':
            present["Number of children over 3 enrolled in nursery school, preschool or kindergarten"] = present[
                                                                                                             'DP02_0054E'] + \
                                                                                                         present[
                                                                                                             'DP02_0053E']
            fig = px.choropleth_mapbox(present, geojson=countytractgeos, locations='TRACTCE',
                                       featureidkey="properties.TRACTCE",
                                       color="Number of children over 3 enrolled in nursery school, preschool or kindergarten",
                                       color_continuous_scale="orrd",
                                       range_color=(0, max(present[
                                                               "Number of children over 3 enrolled in nursery school, preschool or kindergarten"])),
                                       mapbox_style="carto-positron",
                                       zoom=7, center={"lat": lat, "lon": lon},
                                       opacity=0.7,
                                       width=600
                                       ).update_layout(margin={"r": 0, "t": 10, "l": 0, "b": 0})
        content_map_row = dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(id='bigmap', figure=fig)
                )
            ]
        )
        content = html.Div(
            [html.H2(' '),
             content_map_row],
            style=CONTENT_STYLE
        )
    else:
        content = html.Div([html.H2(' '), dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [

                            dbc.CardBody(
                                [
                                    html.H4(children=["Sorry, that indicator can't be mapped right now :("], className='card-title', style=CARD_TEXT_STYLE),
                                    html.P(children=["Try a different one!"], style=CARD_TEXT_STYLE),
                                ]
                            )
                        ], color='#91242b', inverse=True
                    ),
                    md=12
                )
            ]
        )])


    layout = html.Div([content], style=CONTENT_STYLE)
    return layout
