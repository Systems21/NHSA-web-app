# testing census class functions

from itertools import product
from functools import reduce
from multiprocessing import Pool
import pandas as pd
from datetime import date
import censusdata


N_PROCESSES = 4
state_county_fips = pd.read_csv('state_county_fips.csv', dtype=str)
vardf = pd.read_csv('census_vars_V5.csv')


class CensusViewer:
    def __init__(self, api_key):
        self.api_key = api_key
    
    @staticmethod
    def available_categories():
        return sorted(list(vardf.category.unique()))

    @staticmethod
    def _call_census(state_fip, var_ids, src, year, tabletype, api_key):
        """
        Queries census API for county-level data
            geos (list[list[str, str]]): List of state, county name pairs
            census_vars (list[dict]): List of variable specification dicts
            key (str): data.census.gov api key
        """

        # build list of var ids, and dict of id-name mappings

        county_data = censusdata.download(
            src,
            year,
            censusdata.censusgeo([("state", state_fip), ("county", "*")]),
            var_ids,
            key=api_key,
            tabletype=tabletype,
        )
        
        state_data = censusdata.download(
            src,
            year,
            censusdata.censusgeo([("state", state_fip)]),
            var_ids,
            key=api_key,
            tabletype=tabletype,
        )

        return county_data, state_data, year

    def build_dataframe(
        self, county_names, states, selected_cats, descriptions=False, src="acs5"):
        """
        Creates dataframe view of variables in requested counties. Main helper 
        view function, ie does most of the work of munging frontend queries and 
        coordinating lower-level helper functions.
        Does some optimization to run census api queries in parallel. Consider tweaking 
        N_PROCESSES parameter to affect performance.
        args:
            county_names (List[str]): List of county names and their state
            selected_cats (List[str]): List of variable categories of interest
            descriptions (boolean): Boolean controlling whether to include variable
                descriptions in df output (not implemented)
            src (str): Census api source parameter       
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
        # from same year. So we make one call to 
        # censusdata.download for each year x tabletype.  

        # So:
        # 1. get state fip

        state_fip = list(state_county_fips[state_county_fips['State'].isin(states)].State_FIPS.unique())[0]
        if len(state_fip)==1:
            state_fip= '0' + state_fip

        # 2. build list of tabletypes (& corresponding vars)

        tabletype_jobs = []
        for table_prefix, tabletype in tabletypes:

            tabletype_vars = [var for var in all_vars if var.startswith(table_prefix)]

            if tabletype_vars:
                tabletype_jobs.append([tabletype_vars, tabletype])

        # 3. get list of years
        
        year = int(date.today().strftime("%Y"))
        start = year-6
        end = year-1
        years_list = list(range(start,end))

        # 3. cross product: years x tabletypes

        census_jobs = []

        for years, (tabletype_vars, tabletype) in product(
            years_list, tabletype_jobs
        ):
            census_jobs.append(
                [state_fip, tabletype_vars, src, years, tabletype, self.api_key]
            )

        # 4. run all of the downloads (in parallel)

        pool = Pool(N_PROCESSES)

        raw_dfs = pool.starmap(self._call_census, census_jobs)

        # 5. filter counties and merge all - county formatted as list for potential update to allow users to select multiple counties
        geos = []
        for geo in raw_dfs[0][0].index.tolist():
            if geo.name in county_names:
                geos.append(geo)
        
        results = []
        for result in raw_dfs:
            countydat = result[0]
            Fcountydat = countydat[countydat.index.get_level_values(0).isin(geos)]
            TFcountydat = Fcountydat.T
            TFcountydat.columns = county_names
            Tstatedat = result[1].T
            Tstatedat.columns = ['State']
            Tstatedat['Year'] = result[2]
            final = pd.merge(TFcountydat, Tstatedat, left_index=True, right_index=True, how="outer")
            results.append(final)
            
        raw_data = pd.concat(results)
        
        # 6. translate census jargon to plain english variables names
        raw_data['Variable'] = raw_data.apply(lambda x: vardf[vardf['vars'] == x.name]['name'].iloc[0], axis=1)
        raw_data['Category'] = raw_data.apply(lambda x: vardf[vardf['vars'] == x.name]['category'].iloc[0], axis=1)

        return raw_data

    @staticmethod
    def _call_fortracts(state_fip, county_fip, var_ids, src, year, tabletype, api_key):
        """
        Queries census API for tract-level data
        """

        # build list of var ids, and dict of id-name mappings

        tract_data = censusdata.download(
            src,
            year,
            censusdata.censusgeo([("state", state_fip), ("county", county_fip), ("tract", "*")]),
            var_ids,
            key=api_key,
            tabletype=tabletype,
        )
        

        return tract_data, year

    def build_mapping_df(
        self, county_names, state, selected_cats, descriptions=False, src="acs5"):
        """
        Creates dataframe view of variables in requested counties. Main helper 
        view function, ie does most of the work of munging frontend queries and 
        coordinating lower-level helper functions.
        Does some optimization to run census api queries in parallel. Consider tweaking 
        N_PROCESSES parameter to affect performance.
        args:
            county_names (List[str]): List of county names and their state
            selected_cats (List[str]): List of variable categories of interest
            descriptions (boolean): Boolean controlling whether to include variable
                descriptions in df output (not implemented)
            src (str): Census api source parameter       
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
        # from same year. So we make one call to 
        # censusdata.download for each year x tabletype.  

        # So:
        # 1. get state & county fips - county formatted as list for potential update to allow users to select multiple counties

        state_fip = list(state_county_fips[state_county_fips['State']==state].State_FIPS.unique())[0]
        if len(state_fip)==1:
            state_fip= '0' + state_fip

        badcounty_fips = list(state_county_fips[state_county_fips['County'].isin(county_names)].County_FIPS)
        county_fips = []
        for county in badcounty_fips:
            if len(county)==1:
                county_fips.append('00' + county)
            elif len(county)==2:
                county_fips.append('0' + county)
            else:
                county_fips.append(county)
        # 2. build list of tabletypes (& corresponding vars)

        tabletype_jobs = []
        for table_prefix, tabletype in tabletypes:

            tabletype_vars = [var for var in all_vars if var.startswith(table_prefix)]

            if tabletype_vars:
                tabletype_jobs.append([tabletype_vars, tabletype])

        # 3. get two years, five years apart, of most recently available census data
        
        year = int(date.today().strftime("%Y"))
        start = year-6
        end = year-2
        years_list = list((start,end))

        # 3. cross product: years x tabletypes

        census_jobs = []

        for years, (tabletype_vars, tabletype), county in product(
            years_list, tabletype_jobs, county_fips
        ):
            census_jobs.append(
                [state_fip, county, tabletype_vars, src, years, tabletype, self.api_key]
            )

        # 4. run all of the downloads (in parallel)

        pool = Pool(N_PROCESSES)

        raw_dfs = pool.starmap(self._call_fortracts, census_jobs)

        # 5. filter counties and merge all 
        # Note! right now it is setup assuming only one county is selected. If users want to select multiple in the future,
        # this section will need to be reconfigured. 
        geos = []
        for geo in raw_dfs[0][0].index.tolist():
            if geo.name in county_names:
                geos.append(geo)
        
        resultspast = []
        resultspresent = []
        for result in raw_dfs:
            if result[1] == start:
                resultspast.append(result[0])
            elif result[1] == end:
                resultspresent.append(result[0])

        if len(resultspast)==1:
            past = resultspast[0]
            present = resultspresent[0]
        else:
            past = reduce(lambda df1,df2: pd.merge(df1,df2,left_index=True, right_index=True, how="outer"), resultspast)
            present = reduce(lambda df1,df2: pd.merge(df1,df2,left_index=True, right_index=True, how="outer"), resultspresent)
        
        past['Year'] = start
        present['Year'] = end
        # grab the tract numbers into a new column
        tractnums = [place.geo[2][1] for place in past.index]
        past['TRACTCE'] = tractnums
        tractnums = [place.geo[2][1] for place in present.index]
        present['TRACTCE'] = tractnums

        return (present, past, state_fip, county_fips)
