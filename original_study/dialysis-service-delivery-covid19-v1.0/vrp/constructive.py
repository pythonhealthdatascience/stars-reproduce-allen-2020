import numpy as np
import pandas as pd

import vrp.io as io

def single_capacity_cost(warehouse, matrix):
    '''
    Calculate the symmetric cost of single trips
    from a warehouse to each city and back again.

    Parameters:
    -------
    warehouse - int or str
        index / postcode sector of the warehouse. All trips start and finish
        at the warehouse

    matrix - pd.DataFrame
        matrix of travel costs (either distances or times)
    '''
    costs = [io.travel_cost(warehouse, city, matrix) for city in list(matrix.columns)]
    return 2 * np.array(costs).sum()


def pairs_of_savings(warehouse, matrix):
    cities = list(matrix.columns)
    savings = {}
    for i in range(len(cities)):
        for j in range(i+1, len(cities)):
            warehouse_to_i = io.travel_cost(warehouse, cities[i], matrix)
            warehouse_to_j = io.travel_cost(warehouse, cities[j], matrix)
            cost_ij = io.travel_cost(cities[i], cities[j], matrix)
            key = f'{cities[i]}-{cities[j]}'
            saving_ij = warehouse_to_i + warehouse_to_j - cost_ij
            savings[key] = [cities[i], cities[j], saving_ij]

    savings = pd.DataFrame(savings).T
    savings.columns = ['from', 'to', 'saving']
    return savings



def max_savings(n_cities, savings):
    '''
    Choose routes with best savings.

    n_cities - int
        no. cities to visit

    savings - pandas.DataFrame
        list of all routes and savings
    
    '''
    visited = []
    to_return = {}

    while len(visited) < n_cities:
        savings.sort_values(by='saving', ascending=False, inplace=True)
        key = savings.index[0]
        to_return[key] = savings.iloc[0]['saving']
        from_city = savings.iloc[0]['from']
        to_city = savings.iloc[0]['to']

        #remove all to and from
        savings = savings.loc[savings['from'] != from_city]
        savings = savings.loc[savings['from'] != to_city]
        savings = savings.loc[savings['to'] != to_city]
        savings = savings.loc[savings['from'] != to_city]

        #remember cities visited
        visited.append(from_city)
        visited.append(to_city)

    return to_return


def unit_demand(warehouse, cities):
    '''
    Each citiy has demand 1.0 apart
    from warehouse

    Parameters:
    ---------
    warehouse - str or int
    
    cities - list
        list of city identifies (str or int)

    Returns:
    --------
    dict
        'str':float
        city:demand
    '''
    demand = {}
    for city in cities:
        if city != warehouse:
            demand[city] = 1.0
        else:
            demand[city] = 0.0

    return demand


class SequentialClarkeWright(object):
    def __init__(self, warehouse, adjacent_route_func=None, merge_func=None):
        '''
        Sequential Clarke Wright Savings Method.

        Clarke G & Wright JW, 1964, Scheduling of vehicles from a central depot 
        to a number of delivery points, Operations Research, 12(4), pp. 568–581     

        Another useful paper by Graham Rand:
        Life and times of the savings method...
        https://www.ajol.info/index.php/orion/article/view/48716

        Parameters:

        warehouse - str
            warehouse/depot identifier
        
        adjacent_route_func - object (function)

        merge_func - object (function)

        '''

        if adjacent_route_func is None:
            adjacent_route_func = adjacent_route_tail

        if merge_func is None:
            merge_func = merge_tail

        self.warehouse = warehouse
        self.adjacent_route = adjacent_route_func
        self.merge = merge_func
        
        
    def solve(self, vehicle_capacity, demand, matrix):
        '''
        Sequential creation of journeys using the savings method of  
        Clarke and Wright (1964).

        Dev notes:
        * This code works, but needs refactoring
        * This is a bit of a clumsy heuristic, although it works.
        * Parallel version of the algorithm might be cleaner.
        
        Paramaters:
        ---------
        demand - dict
            demand at each node

        vehicle_capacity - float
            carrying capacity of (single type of) vehicles

        Returns:
        -------
        list of dicts
            each dict is a vehicle journey through cities (excluding warehouse)
            along with information about the journey.
        '''
        #step 1: get the savings matrix
        savings = pairs_of_savings(self.warehouse, matrix)

        #step 2: sort the savings into accending order...
        savings.sort_values(by='saving', ascending=False, inplace=True)

        #delete all zero savings (to and from warehouse)
        savings = savings.loc[savings['saving'] > 0.0]
        
        #step 3: started from the largest saving then sequentially 
        #build each route.
        journeys = []

        #dev note.  Is there a cleaner way to code this instead of using
        #just savings and cities_allocated.
        savings_allocated = []
        cities_allocated = []
        
        for i in range(len(savings)):

            #if this pair of cities has not already been allocated
            if savings.index[i] not in savings_allocated and \
                savings.iloc[i]['from'] not in cities_allocated and \
                    savings.iloc[i]['to'] not in cities_allocated:
                
                demand_ij = demand[savings.iloc[i]['from']] + \
                            demand[savings.iloc[i]['to']]

                current_route = {'route':savings.index[i], 
                                'from':savings.iloc[i]['from'], 
                                'to':savings.iloc[i]['to'], 
                                'demand':demand_ij,
                                'cities':[savings.iloc[i]['from'], 
                                        savings.iloc[i]['to']]}

                #not sure I need both....a bit clumsy.
                savings_allocated.append(current_route['route'])
                cities_allocated.append(current_route['from'])
                cities_allocated.append(current_route['to'])

                #instead of step down get 
                #step down remaining savings table
                for row in range(i+1, len(savings)):

                    link = savings.iloc[row].to_dict()

                    #if both cities have already been allocated then eliminate
                    if both_cities_already_allocated(link, cities_allocated, 
                                                     current_route['cities']):
                        savings_allocated.append(savings.index[row])
                        #skip this loop
                        continue

                    #if capacity remains for journey 
                    if current_route['demand'] < vehicle_capacity:

                        if self.adjacent_route(link['from'], link['to'], 
                                               current_route):
                            
                            merge_accepted, new_route = self.merge(current_route,
                                                                   link,
                                                                   demand,
                                                                   vehicle_capacity)

                            if merge_accepted:
                                savings_allocated.append(savings.index[row])
                                current_route = new_route
                        
                    else:
                        break

                journeys.append(current_route)
                #remember cities allocated.
                [cities_allocated.append(i) for i in current_route['cities']]

        journeys = self._add_odd_route(cities_allocated, 
                                       matrix, 
                                       demand, 
                                       journeys, 
                                       vehicle_capacity)
        return journeys

    def _add_odd_route(self, cities_allocated, matrix, demand, journeys, 
                       vehicle_capacity):
        '''
        Sometimes a single route remains and needs to be added at the end.
        '''
        cities = list(matrix.columns)
        cities = [city for city in cities if city != self.warehouse]
        for city in cities:
            if city not in cities_allocated:
                additional_load = demand[city]
                if journeys[-1:][0]['demand'] + additional_load <= vehicle_capacity:
                    journeys[-1:][0]['demand'] += + additional_load
                    journeys[-1:][0]['route'] += '-' + city
                    return journeys
                else:
                    route = {}
                    route['route'] = city
                    route['demand'] = demand[city]
                    journeys.append(route)
                    return journeys
        
        return journeys
                


def both_cities_already_allocated(link, other_routes, route):
    if link['to'] in other_routes and link['from'] in other_routes:
        return True
    elif link['to'] in route and link['from'] in route:
        return True
    return False

def merge_head_tail(route, to_link, demand, vehicle_capacity):
    '''
    Tentively merge routes

    Parameters:
    ----------
    route - dict

    to_link - dict

    demand - dict
    '''
    #decide if head or tail

    new_route = {}
    #head
    if route['from'] == to_link['to']:
        #check 'from' is not already within the route
        if to_link['from'] not in route['cities']:
            additional_demand = demand[to_link['from']]
            if route['demand'] + additional_demand <= vehicle_capacity:
                new_route['route'] = to_link['from'] + '-' + route['route'] 
                new_route['from'] = to_link['from']
                new_route['to'] = route['to']
                new_route['demand'] = route['demand'] + additional_demand
                new_route['cities'] = route['cities']
                add_cities_to_route(new_route, to_link)
                return True, new_route

    elif route['from'] == to_link['from']:
        #check 'to' is not already within the route
        if to_link['to'] not in route['cities']:
            additional_demand = demand[to_link['from']]
            if route['demand'] + additional_demand <= vehicle_capacity:
                new_route['route'] = to_link['to'] + '-' + route['route'] 
                new_route['from'] = to_link['to']
                new_route['to'] = route['to']
                new_route['demand'] = route['demand'] + additional_demand
                new_route['cities'] = route['cities']
                add_cities_to_route(new_route, to_link)
                return True, new_route

    elif route['to'] == to_link['to']:
        #check 'from' is not already within the route
        if to_link['from'] not in route['cities']:
            additional_demand = demand[to_link['from']]
            if route['demand'] + additional_demand <= vehicle_capacity:
                new_route['route'] = route['route'] + '-' + to_link['from'] 
                new_route['from'] = to_link['from']
                new_route['to'] = to_link['to']
                new_route['demand'] = route['demand'] + additional_demand
                new_route['cities'] = route['cities']
                add_cities_to_route(new_route, to_link) 
                return True, new_route
    #tail
    else:
        #check_tail is not already within the route
        if to_link['to'] not in route['cities']:
            additional_demand = demand[to_link['to']]
            if route['demand'] + additional_demand <= vehicle_capacity:
                new_route['route'] = route['route'] + '-' + to_link['to']
                new_route['to'] = to_link['to']
                new_route['from'] = route['from']
                new_route['demand'] = route['demand'] + additional_demand
                new_route['cities'] = route['cities']
                add_cities_to_route(new_route, to_link)
                return True, new_route
    
    return False, None


def merge_tail(route, to_link, demand, vehicle_capacity):
    '''
    Tentively merge routes

    Only merges at tail of route 

    Parameters:
    ----------
    route - dict

    to_link - dict

    demand - dict
    '''
    #decide if head or tail

    new_route = {}
    if route['to'] == to_link['to']:
        #check 'from' is not already within the route
        if to_link['from'] not in route['cities']:
            additional_demand = demand[to_link['from']]
            if route['demand'] + additional_demand <= vehicle_capacity:
                new_route['route'] = route['route'] + '-' + to_link['from'] 
                new_route['from'] = to_link['from']
                new_route['to'] = to_link['to']
                new_route['demand'] = route['demand'] + additional_demand
                new_route['cities'] = route['cities']
                add_cities_to_route(new_route, to_link) 
                return True, new_route
    #tail
    elif route['to'] == to_link['from']:
        #check_tail is not already within the route
        if to_link['from'] not in route['cities']:
            additional_demand = demand[to_link['to']]
            if route['demand'] + additional_demand <= vehicle_capacity:
                new_route['route'] = route['route'] + '-' + to_link['to']
                new_route['to'] = to_link['to']
                new_route['from'] = route['from']
                new_route['demand'] = route['demand'] + additional_demand
                new_route['cities'] = route['cities']
                add_cities_to_route(new_route, to_link)
                return True, new_route
    
    return False, None

def add_cities_to_route(route, link):
    if link['from'] not in route['cities']:
        route['cities'].append(link['from'])
    
    if link['to'] not in route['cities']:
        route['cities'].append(link['to'])
    
def adjacent_route_head_tail(from_city, to_city, route):
    '''
    is the head or tail of the route adjacent to either the from
    or to city?
    '''
    if((route['from'] == from_city) and (route['to'] == to_city)):
        return False
    elif((route['from'] == to_city) and (route['to'] == from_city)):
        return False
    elif ((route['to'] == from_city) or (route['to'] == to_city) or 
         (route['from'] == from_city) or (route['from'] == to_city)):
        #catch if cities in pair has already both been allocated...
        if to_city in route['cities'] and from_city in route['cities']:
            return False
        return True
    else:
        return False


def adjacent_route_tail(from_city, to_city, route):
    '''
    is the tail of the route adjacent to either the from
    or to city?
    '''
    if ((route['to'] == from_city) or (route['to'] == to_city)):
        #catch if cities in pair has already both been allocated...
        if to_city in route['cities'] and from_city in route['cities']:
            return False
        return True
    else:
        return False