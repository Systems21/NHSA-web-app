from itertools import product
from functools import reduce
from multiprocessing import Pool
import pandas as pd
import censusdata


N_PROCESSES = 4
state_county_fips = pd.read_csv('state_county_fips.csv', dtype=str)
vardf = pd.read_csv('census_vars_V2.csv')

class CensusViewer:
    def __init__(self, api_key):
        self.api_key = api_key
    
    @staticmethod
    def available_categories():
        return sorted(list(vardf.category.unique()))

    @staticmethod
    def _build_state_dataframe(state_fips, var_ids, src, year, tabletype, api_key):
        """
        Queries census API for county-level data
            geos (list[list[str, str]]): List of state, county name pairs
            census_vars (list[dict]): List of variable specification dicts
            key (str): data.census.gov api key
        """

        # build list of var ids, and dict of id-name mappings

        state_data = censusdata.download(
            src,
            year,
            censusdata.censusgeo([("state", state_fips), ("county", "*")]),
            var_ids,
            key=api_key,
            tabletype=tabletype,
        )

        return state_fips, state_data

    def _build_dataframe(
        self, county_names, states, selected_cats, descriptions=False, src="acs5", year=2019
    ):
        """
        Creates dataframe view of variables in requested counties. Main helper 
        view function, ie does most of the work of munging frontend queries and 
        coordinating lower-level helper functions.
        Does some optimization to run census api queries in parallel. Consider tweaking 
        N_PROCESSES parameter to affect performance.
        args:
            county_names (List[str]): List of state, county name pairs
            selected_vars (List[Dict]): List of variable dicts
            descriptions (boolean): Boolean controlling whether to include variable
                descriptions in df output (not implemented)
            src (str): Census api source parameter
            year (int): Census api year parameter        
        """

        # generate list of selected census api variable ids

        all_vars = list(vardf[vardf.category.isin(selected_cats)].vars)

        tabletypes = [
            ("B", r"detail"),
            ("S", r"subject"),
            ("DP", r"profile"),
            ("CP", r"cprofile"),
        ]

        # Within one census api query, all vars must be from same table type &
        # all counties must be from same state. So we make one call to 
        # censusdata.download for each state x tabletype.  

        # So:
        # 1. build list of states

        raw_fips = list(state_county_fips[state_county_fips['State'].isin(states)].State_FIPS.unique())
        state_fips = []
        for fip in raw_fips:
            if len(fip)==2:
                state_fips.append(fip)
            elif len(fip) != 2:
                state_fips.append('0' + fip)

        # 2. build list of tabletypes (& corresponding vars)

        tabletype_jobs = []
        for table_prefix, tabletype in tabletypes:

            tabletype_vars = [var for var in all_vars if var.startswith(table_prefix)]

            if tabletype_vars:
                tabletype_jobs.append([tabletype_vars, tabletype])

        # 3. cross product: states x tabletypes

        census_jobs = []

        for state_fips, (tabletype_vars, tabletype) in product(
            state_fips, tabletype_jobs
        ):
            census_jobs.append(
                [state_fips, tabletype_vars, src, year, tabletype, self.api_key]
            )

        # 4. run all of the downloads (in parallel)

        pool = Pool(N_PROCESSES)

        raw_dfs = pool.starmap(self._build_state_dataframe, census_jobs)

        # 5. merge all

        merged_state_dfs = []
        for state in set(state for state, _ in raw_dfs):
            raw_state_dfs = [
                state_data for state_, state_data in raw_dfs if state_ == state
            ]
            merged_state_df = reduce(
                lambda x, y: pd.merge(
                    x, y, left_index=True, right_index=True, how="outer"
                ),
                raw_state_dfs,
            )

            merged_state_dfs.append(merged_state_df)

        merged_dfs = pd.concat(
            merged_state_dfs,
        )

        # 6. filter on counties

        raw_data = (
            merged_dfs.assign(county=merged_dfs.index.map(lambda x: x.name))
            .set_index("county")
            .filter([f"{county}, {state}" for state, county in county_names], axis=0)
        )

        return raw_data

    def view_df(self, county_names, states, selected_cats):

        """
        Builds view of census data stored in a Pandas dataframe
        Args:
            county_names (list[list(str, str)]): List of county, state name pairs
            src (str): data.census.gov API source to be used. (currently unused)
            year (int): Year to query census data. (currently unused)
        returns Pandas.DataFrame
        """
        fulldf = self._build_dataframe(county_names, states, selected_cats)
        # translate census jargon var names to descriptive features
        vars_english = {id: vardf[vardf['vars'] == id]['name'].tolist()[0] for id in fulldf.columns}
        fulldf = fulldf.rename(columns = vars_english).transpose()
        fulldf["Variable"] = fulldf.index
        fulldf = fulldf.merge(vardf[['name', 'category']], left_on = "Variable", right_on = "name", how = "left").drop(columns=['name'])
        first_col = fulldf.pop('Variable')
        fulldf.insert(0, 'Variable', first_col)
        return fulldf