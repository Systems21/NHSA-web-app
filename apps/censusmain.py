import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from app import app
from census import CensusViewer
from load_configcustom import load_config
import pathlib

# configure data
# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("..").resolve()
# Create dataframe for simple selections and filters
state_county_choices = pd.read_csv(DATA_PATH.joinpath("state_county_fips.csv"))

# setup census viewer
censusViewer = CensusViewer(vars_config=load_config("vars.json"), api_key='')

# List of variable category choices
vars = censusViewer.available_vars
varcategories = [var[0] for var in vars]

# the style arguments for the sidebar.
SIDEBAR_STYLE = {
    'position': 'fixed',
    'left': 0,
    'width': '20%',
    'padding': '20px 10px',
    'background-color': '#f8f9fa'
}

# the style arguments for the main content page.
CONTENT_STYLE = {
    'margin-left': '25%',
    'margin-right': '5%',
    'padding': '20px 10p'
}

TEXT_STYLE = {
    'textAlign': 'center',
    'color': '#191970'
}

CARD_TEXT_STYLE = {
    'textAlign': 'center',
    'color': '000000'
}

controls = dbc.FormGroup(
    [
        html.P('Pick States', style={
            'textAlign': 'center'
        }),
        dcc.Dropdown(
            id='states-dropdown', value=None, clearable=False,
            options=[{'label': x, 'value': x} for x in state_county_choices["State"].unique()],
            multi=True
        ),
        html.Br(),
        html.P('Pick Counties', style={
            'textAlign': 'center'
        }),
        dcc.Dropdown(
            id='county-dropdown', value='Autauga County, Alabama', clearable=False,
            options=[],
            multi=True
        ),
        html.P('Pick Years', style={
            'textAlign': 'center'
        }),
        dbc.Card([dbc.Checklist(
            id='check_list',
            options=[{
                'label': '2018',
                'value': 'value1'
            },
                {
                    'label': '2019',
                    'value': 'value2'
                },
                {
                    'label': '2020',
                    'value': 'value3'
                }
            ],
            value=['value1', 'value2'],
            inline=True
        )]),
        html.Br(),
        html.P('Pick Variable Categories', style={
            'textAlign': 'center'
        }),
        dcc.Dropdown(
            id='vars-dropdown', placeholder="Select variables",
            persistence=True, persistence_type='memory',
            options=[{'label': x, 'value': x} for x in varcategories],
            multi=True
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

sidebar = html.Div(
    [
        html.H3('Filter a Data Selection', style=TEXT_STYLE),
        html.Hr(),
        controls
    ],
    style=SIDEBAR_STYLE,
)

content_first_row = dbc.Row(
    [
        dbc.Col(
            dcc.Graph(id='graph_1'), md=4
        ),
        dbc.Col(
            dcc.Graph(id='graph_2'), md=4
        ),
        dbc.Col(
            dcc.Graph(id='graph_3'), md=4
        )
    ]
)

content_second_row = dbc.Row([
    dbc.Col(
        dbc.Card(
            [

                dbc.CardBody(
                    [
                        html.H4(id='card_title_1', children=['Insight 1'], className='card-title',
                                style=CARD_TEXT_STYLE),
                        html.P(id='card_text_1', children=['This chart shows us'], style=CARD_TEXT_STYLE),
                    ]
                )
            ], color='#a9dad6'
        ),
        md=4
    ),
    dbc.Col(
        dbc.Card(
            [

                dbc.CardBody(
                    [
                        html.H4('Insight 2', className='card-title', style=CARD_TEXT_STYLE),
                        html.P('This chart shows us', style=CARD_TEXT_STYLE),
                    ]
                ),
            ], color='#e54e4b'

        ),
        md=4
    ),
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
        md=4
    )
])

content_third_row = dbc.Row(
    [
        dbc.Col(
            dash_table.DataTable(id='table', columns=[], data=[],
                                 style_cell={'textAlign': 'left'},
                                 export_format="csv", ), md=12,
        )
    ]
)

# content_fourth_row = dbc.Row(
#     [
#         dbc.Col(
#             dcc.Graph(id='graph_5'), md=6
#         ),
#         dbc.Col(
#             dcc.Graph(id='graph_6'), md=6
#         )
#     ]
# )

content = html.Div(
    [
        html.H3('Census Results', style=TEXT_STYLE),
        content_first_row,
        content_second_row,
        content_third_row
        #content_fourth_row
    ],
    style=CONTENT_STYLE
)

layout = html.Div([sidebar, content])



# Populate the counties dropdown with options and values
@app.callback(
    Output('county-dropdown', 'options'),
    Input('states-dropdown', 'value'),
)
def set_county_options(chosen_state):
    dff = state_county_choices[state_county_choices['State'].isin(chosen_state)]
    counties_of_states = [{'label': c, 'value': c} for c in dff["County"]]
    return counties_of_states

# Populate the counties dropdown with options and values
@app.callback(
    Output('table', 'columns'),
    Output('table', 'data'),
    Input('vars-dropdown', 'value'),
    Input('county-dropdown', 'value'),
)
def fill_table(svars, scounties):
    # Pull details for selected var categories
    varlist = [t for t in vars if t[0] in svars]
    # Pull list of var ids for data extraction
    selected_ids = []
    for var in varlist:
        for pair in var[1]:
            tempdict = pair[0]
            id = tempdict.get('value')
            selected_ids.append(str(id))
    selected_counties = [[state.strip(), county] for county, state in [county.split(",") for county in scounties]]
    fulldf = censusViewer.view_df(county_names=selected_counties, selected_var_ids=selected_ids)
    cols = [{"name": i, "id": i} for i in fulldf.columns]
    cols[0]['name'] = 'Variable'
    dat = fulldf.to_dict('records')
    return cols, dat
