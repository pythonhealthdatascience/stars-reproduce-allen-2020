import pandas as pd

class Dialysis_units:
    """
    Class to hold unit information loaded from CSV. 
    Ranks units by proximity (travel time) and by prescribed order (for COVID +ve
    patients).
    
    Object attributes
    -----------------
    
    location_lookup: dictionary linking subunit (key) to unit postocde (value)
    number_of_units: toal number of subunits
    travel_times: import of travel times between patient postcode sectors and units
    unit_info: import of unit info csv
    unit_list: list of subunits
    unit_location: list of subunit locations
    
    
    Methods
    -------
    
    rank_units_by_travel_time:
        For each patient location ranks choice of unit by travel time (lowest first). 
        Stores results in a DataFrame.
    
    rank_cov_units_by_entered_order
    
    
    """
    def __init__(self, env):
        """Constructor for dialysis unit"""
        
        self.unit_info = pd.read_csv('sim/units.csv')
        self.travel_times = pd.read_csv('sim/travel_matrix.csv', index_col='from_postcode')
        self.rank_units_by_travel_time()
        self.rank_cov_units_by_entered_order()
        self.unit_list = list(self.unit_info.subunit)
        self.unit_location = list(self.unit_info.Location)
        self.number_of_units = len(self.unit_list)
        
        # Create lookup table for subunit location
        self.location_lookup = dict(zip(self.unit_list, self.unit_location)) 

        
    def rank_units_by_travel_time(self):
        """For each patient location ranks choice of unit by travel time (lowest first). 
        Stores results in a DataFrame."""
        
        # Create dictionaly linking subunit name to location
        lookup = self.unit_info[['Location', 'subunit']]
        lookup.set_index('Location', inplace=True)
                
        # For each patient location order units by proximity to patient postcode
        cols = range(lookup.shape[0])
        self.unit_preferences = pd.DataFrame(columns = cols)    
        for key, value in self.travel_times.iterrows():
            # Sort travel times to locations, and lookup subunits in location
            value.sort_values(inplace=True)
            value_dict = {x:y for x,y in enumerate(value.index)}
            location_series = pd.Series(data=value_dict, name=key)
            subunit_series = lookup.loc[location_series]
            flat_list = [item for sublist in subunit_series.values for item in sublist]
            row_to_add = {x:flat_list[x] for x in cols}
            self.unit_preferences = self.unit_preferences.append(row_to_add, ignore_index=True)
            
        self.unit_preferences['patient_location'] = self.travel_times.index
        self.unit_preferences.set_index('patient_location', inplace=True)
        
            
    def rank_cov_units_by_entered_order(self):
        """
        Filters and sorts units for allocation of COVID+ patients. Order read from CSV.
        """
        
        mask = self.unit_info['Cov +ve order'] > 0
        # Sort only if some units are listed as being preferred
        if mask.sum() > 0:
            self.given_order = list(self.unit_info[mask].sort_values('Cov +ve order')['subunit'])
