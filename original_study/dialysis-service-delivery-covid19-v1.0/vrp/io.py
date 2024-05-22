import pandas as pd
import numpy as np

PATH_MIN = 'patient_geography_data/travel_matrix_time_min.csv'
PATH_KM = 'patient_geography_data/travel_matrix_distance_km.csv'
PATH_RAND = 'patient_geography_data/rand.csv'
PATH_RAND_DEMAND = 'patient_geography_data/rand_demand.csv'
PATH_POSTCODE_COUNT = 'patient_geography_data/patient_postcode_count.csv'
PATH_PC_NO_HOME_NO_IOW = 'patient_geography_data/patient_counts_no_home_or_IOW.csv'


def load_patient_postcode_count(exclude_home_and_iow=True):
    '''
    Read patient postcode sector count
    from file.
    
    Returns:
    ---------
    pandas.DataFrame
    '''
    if exclude_home_and_iow:
        path = PATH_PC_NO_HOME_NO_IOW
    else:
        path = PATH_POSTCODE_COUNT

    return pd.read_csv(path, 
                       index_col='sector',
                       skipinitialspace=True)

def load_travel_time():
    '''
    Read full travel time matrix
    from file.
    
    Returns:
    ---------
    pandas.DataFrame
    '''
    return pd.read_csv(PATH_MIN, 
                       index_col='from_postcode',
                       skipinitialspace=True)

def load_travel_distance():
    '''
    read full travel distance matrix from file

    Returns:
    ---------
    pandas.DataFrame
    '''
    return pd.read_csv(PATH_KM, 
                       index_col='from_postcode',
                       skipinitialspace=True)  


def load_toy_data():
    '''
    Read full travel time matrix
    from file.
    
    Returns:
    ---------
    pandas.DataFrame
    '''
    matrix =  pd.read_csv(PATH_RAND, 
                       index_col='Locations',
                       skipinitialspace=True)
    
    demand =  pd.read_csv(PATH_RAND_DEMAND, 
                          index_col='Customer',
                          skipinitialspace=True)

    return matrix, demand[demand.columns[0]].T.to_dict()



def trim_matrix(matrix, sectors):
    '''
    Trim the full matrix to a limited
    number of postcode sectors

    Parameters:
    --------
    matrix - pd.DataFrame,
        Full travel time/distance matrix

    sectors - list
        List of postcode sectors 

    Returns:
    -------
    pandas.DataFrame
    '''
    trimmed = matrix.loc[sectors]
    trimmed = trimmed[sectors]
    return trimmed

def route_cost(warehouse, route, matrix):
    cities = route.split('-')
    #top and tail with warehouse
    cities.insert(0, warehouse)
    cities.append(warehouse)
    cost = 0.0
    for i in range(len(cities)-1):
        cost += travel_cost(cities[i], cities[i+1], matrix)
        
    #cost += travel_cost(cities[-1:], cities[0], matrix)
    return cost

def travel_cost(city_1, city_2, matrix, symmetric=True):
    '''
    Get cost of travelling from city_1 to city_2

    Parameters:
    -----
    city_1 - int  or str
        index/postcode sector of the first city
    
    city_2 - int 
        index/postcode sector of the second city

    matrix - pd.DataFrame
        travel cost matrix
    
    symmetric - bool (default=True)
        enforce symmetic tours.  Routino produces
        asymmetric distances/times.  Set to true
        to make sure that lowest city index is used
        as row lookup and highest as column. This ensures
        a symmetric cost i.e. city_1 -> city_2 == city_2 -> city_1
    
    Returns:
    -------
    float
        scalar representing cost

    Examples:
    -------
    #get cost by index
    matrix = load_travel_distance()
    city_1 = 0
    city_2 = 1
    cost = travel_cost(city_1, city_2, matrix)
    print(cost)

    #get cost by postcode sector string
    matrix = load_travel_distance()
    city_1 = 'BA120' 
    city_2 = 'BA126'
    cost = travel_cost(city_1, city_2, matrix)
    print(cost)
    '''
    if symmetric:
        city_1, city_2 = enforce_symmetry(city_1, city_2)

    if type(city_1) == str:
        found = matrix.at[city_1, city_2]
        return found
    else:
        return matrix.iat[city_1, city_2]

def enforce_symmetry(city_1, city_2):
    '''
    Routino distances/times are not symmetric (but close!)
    This makes sure that the index row city is always the lowest
    index in the lookup.  Works for both postcode sector strings
    and indexes

    Parameters:
    -----
    city_1 - int  or str
        index/postcode sector of the first city
    
    city_2 - int 
        index/postcode sector of the second city

    Returns:
    -------
    Tuple 
    '''

    if city_1 > city_2:
        city_1, city_2 = city_2, city_1
    return city_1, city_2


if __name__ == '__main__':
    df = load_travel_distance()
    sectors = ['BA120', 'BA126', 'BA128', 'BA129']
    trimmed = trim_matrix(df, sectors)
    cost = travel_cost(0, 1, trimmed)
    cost2 = trimmed.loc['BA120']['BA126']
    cost3 = travel_cost('BA120', 'BA126', trimmed)

    print(trimmed)
    print(cost)
    print(cost2)
    print(cost3)
    print(trimmed.loc['BA120'])
    print(trimmed.loc['BA120'].sum() * 2)

