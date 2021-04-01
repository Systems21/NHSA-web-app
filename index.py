import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import pandas as pd
from census import CensusViewer
from layout_styles import SIDEBAR_STYLE, TEXT_STYLE
# Connect to main app.py file
from app import app
from app import server

# Connect to app pages
from apps import home, mapviz, fulldatatable, vardetails, contactinfo
# read in state and county FIPS codes
state_county_choices = pd.read_csv("state_county_fips.csv")
# read in variable choices
vardf = pd.read_csv('census_vars_V5.csv')
# setup census viewer
censusViewer = CensusViewer(api_key='')
# List of variable category choices
varcategories = censusViewer.available_categories()

# Define controls for user filters
controls = dbc.FormGroup(
    [
        html.P('Pick State', style={
            'textAlign': 'center'
        }),
        dcc.Dropdown(
            id='states-dropdown', value=None, clearable=False,
            options=[{'label': x, 'value': x} for x in state_county_choices["State"].unique()],
            multi=False,
            persistence=True
        ),
        html.Br(),
        html.P('Pick County', style={
            'textAlign': 'center'
        }),
        # The options for counties are generated based on the user's state selection
        dcc.Dropdown(
            id='county-dropdown', value=None, clearable=False,
            options=[],
            multi=False,
            persistence=True
        ),
        html.Br(),
        html.P('Pick Variable Categories', style={
            'textAlign': 'center'
        }),
        dcc.Dropdown(
            id='vars-dropdown', value=['Race and Ethnicity'],
            persistence=True, persistence_type='memory',
            options=[{'label': x, 'value': x} for x in varcategories],
            multi=True,
        ),
        html.Br(),
        dbc.Button(
            id='submit_button',
            n_clicks=0,
            children='Submit',
            color='primary',
            block=True
        ),
    ]
)
# Compile sidebar
sidebar = html.Div(
    [
        html.H3('Filter a Data Selection', style=TEXT_STYLE),
        html.Hr(),
        controls
    ],
    style=SIDEBAR_STYLE,
)
# static layout of links & sidebar that persist across pages
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div([
        dcc.Link('Data Insights |', href='/apps/home'),
        dcc.Link(' Map |', href='/apps/mapviz'),
        dcc.Link(' Raw Data |', href='/apps/fulldatatable'),
        dcc.Link(' Variable Details |', href='/apps/vardetails'),
        dcc.Link(' Contact ', href='/apps/contactinfo'),
    ], style={'font-size': 'xx-large'}),
    html.Div([html.Img(id="logo", src=app.get_asset_url("NHSAlogo.png"))], style={'position': 'fixed', 'top':0, 'right':0}),
    html.Div([sidebar]),
    html.Div(id='page-content', children=[])
])

# Populate the counties dropdown with options and values based on state selection
@app.callback(
    Output('county-dropdown', 'options'),
    Input('states-dropdown', 'value'),
)
def set_county_options(chosen_state):
    dff = state_county_choices[state_county_choices['State']==chosen_state]
    counties_of_states = [{'label': c, 'value': c} for c in dff["County"]]
    return counties_of_states

# dynamic content for each page based on filter selections
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname'),
               Input('vars-dropdown', 'value'),
               Input('county-dropdown', 'value'),
               Input('states-dropdown', 'value')])
def display_page(pathname, svars, scounties, sstates):
    # format user selections for census api calls
    fulldf = censusViewer.build_dataframe(county_names=[scounties], states=[sstates], selected_cats=svars)
    cols = [{"name": i, "id": i} for i in fulldf.columns]
    dat = fulldf.to_dict('records')
    if pathname == '/apps/home':
        return home.return_insights(fulldf)
    if pathname == '/apps/mapviz':
        return mapviz.layout
    if pathname == '/apps/fulldatatable':
        return fulldatatable.return_content(cols, dat)
    if pathname == '/apps/vardetails':
        return vardetails.return_contentvars(highlightcats=svars)
    if pathname == '/apps/contactinfo':
        return contactinfo.layout
    else:
        return home.return_insights(fulldf)


if __name__ == '__main__':
    app.run_server(debug=True)
