from dataclasses import dataclass

from joblib import Parallel, delayed

import numpy as np
import pandas as pd

import vrp.constructive as c
import vrp.io as io

from vrp.metapy.tsp.objective import (SimpleTSPObjective, 
                                      CVRPUnitDemandObjective)

from vrp.metapy.tsp.bruteforce import BruteForceSolver
from vrp.metapy.local_search.random_restarts import (IteratedLocalSearch, 
                                                     EpsilonGreedyHomeBase)

from vrp.metapy.local_search.local_search_2opt import OrdinaryDecent2Opt

DEBUG = True

@dataclass(frozen=True)
class Scenario:
    n_patients: int
    warehouse: str
    vehicle_capacities: list
    postcode_distribution: np.array
    cost_matrix: pd.DataFrame
    p_positive: float = 0.3
    p_transport: float = 0.75
    

def create_postcode_distribution(postcode_count):
    '''
    Adds an additional 'prob' columns to a pandas dataframe
    of postcode sectors and counts of patients living in them.
    '''
    total = postcode_count['count'].sum()
    postcode_count['prob'] = postcode_count['count'] / total
    return postcode_count


class TransportExperiment(object):
    '''
    Stochastic model.

    Simulates a distribution of journeys (for differt patien transport 
    capacities) to transport patients from home to hospital for dialysis 
    (at the moment the model only consider transporting patients TO hospital.
    There is no return journey scheduling.)

    IMPORTANT: The purpose of the model is to give an idea of the feasibility 
    of tranport given the infected population and transport capacity.

    1. samples covid patients that require transport
    2. solves deterministic routing problem specified capacities [1, 2, 3, 4]
    3. can be run multiple times for difference scenarios to find distribution
       of travel journals.

    '''
    def __init__(self, scenario, solver, verbose=False):
        '''
        Constructor method

        Parameters:
        -------
        scenario - Scenario dataclass
            experiment parameters
        
        solver - object 
            routing heuristic object that implements
            .solve(int, dict) 

        '''
        self._params = scenario
        self._solver = solver
        self._verbose = verbose
        
    def single_replication(self):
        '''
        runs a single replication of the model.

        sample covid positive patients that need transport
        constructs routes to transport each patient to the hospital 
        for different capacities.

        '''
        #step 1: sample n patients that need transport
        patients = self._sample_patients(self._params.n_patients)
        
        
        #step 2: sample which patients need transport
        transport_patients = self._sample_transport(self._params.p_transport,
                                                    self._params.n_patients)

        #step 3: sample covid-19 positive patients
        covid_patients = self._sample_covid(self._params.p_positive,
                                            self._params.n_patients)

        #step 4: covid_positive patients that need transport
        covid_patient_mask = transport_patients * covid_patients
        covid_patient_sectors = patients[covid_patient_mask.astype(bool)]

        #step 5: unit demand (simplification at this point)
        demand = demand_by_sector(self._params.warehouse, 
                                        covid_patient_sectors)
        
        #step 6: trim the matrix to help with debug and efficiency
        unique_sectors = list(demand.keys())
        if self._params.warehouse not in unique_sectors:
            unique_sectors.append(self._params.warehouse)

        #6.1 create smaller matrix using unique sectors.
        sub_matrix = io.trim_matrix(self._params.cost_matrix, 
                                    unique_sectors)

        #6.2 clone areas with multiple demands
        #This because sector demand may exceed vehicle_capacity.
        #This workaround allows multiple trips to same postcode sector
        demand, sub_matrix = clone_sectors_with_multiple_demands(demand,
                                                sub_matrix,
                                                intra_sector_travel_cost=5.0)

        #6.3 sort columns and index (incase enforcing symmetry)
        sub_matrix = sort_cost_matrix_lexographically(sub_matrix)

        #step 7: for each capacity, create routes and record total cost.
        costs = {}
        costs['capacity_1'] = c.single_capacity_cost(self._params.warehouse, 
                                                   sub_matrix)
        for capacity in self._params.vehicle_capacities:
            costs[f'capacity_{capacity}'] = []
            journeys = self._solver.solve(vehicle_capacity=capacity, 
                                          matrix=sub_matrix, 
                                          demand=demand)

            costs[f'capacity_{capacity}'] = self.total_routing_cost(journeys,
                                                                    sub_matrix)
        return costs

    def total_routing_cost(self, journeys, matrix):
        '''
        journeys - dict
        '''
        total_cost = 0.0
        for journey in journeys:
            cost = io.route_cost(self._params.warehouse, journey['route'], 
                                 matrix)
            total_cost += cost
            if self._verbose:
                print(journey['route'], end= ' ')
                print(f"load: {journey['demand']}", end=' ')
                print(f"cost: {cost}")
        
        if self._verbose:
            print(f'total cost: {total_cost}')

        return total_cost

    def _sample_transport(self, p_transport, n_patients):
        return np.random.binomial(n=1, p=p_transport, size=n_patients)

    def _sample_covid(self, p_positive, n_patients):
        return np.random.binomial(n=1, p=p_positive, size=n_patients)

    def _sample_patients(self, n_patients):
        '''sample the patients'''
        sample = self._params.postcode_distribution.sample(n=n_patients,
                                                            replace=True,
                                                            weights='prob')
        #get the postcode sectors
        patients = np.array(list(sample.T.columns))
        return np.char.replace(patients, ' ', '') 

def demand_by_sector(warehouse, sectors):
    '''
    Sum over postcode sectors
    
    Parameters:
    ---------
    warehouse - str
        The warehouse key

    sectors - array-like 
        list of non-unique postcode sectors

    Returns:
    --------
    dict - str:int
            sector:no. patients
    '''
    cp = pd.Series(sectors)
    cp.name = 'sector'

    demand = cp.groupby(by=cp).count().to_dict()
    
    if warehouse in demand:
        demand[warehouse] = 0

    return demand


def clone_sectors_with_multiple_demands(demand, matrix,
                                        intra_sector_travel_cost=0.0):
    '''
    Some heuristics cannot handle demands larger than vehicle capacity.
    This method clones sectors to workaround that problem.  

    E.g.  Sector:'ST170', Demand:3
    
    After cloning becomes:  

    Sector:'ST170', Demand:1

    Sector:'ST170_1', Demand:1  (clone)

    Sector:'ST170_2', Demand:1  (clone)

    The travel time between these sectors is set to the value of 
    intra_sector_travel_cost

    Parameters:
    ---------
    demand - dict str:int
        dict key=postcode sectors, value=covid patients in sector

    matrix - pd.DataFrame
        travel costs

    intra_sector_travel_cost - float (optional default = 0.0) 
        pickups within a postcode sector are unlikely to be at
        the same location.  This optional parameter can be set
        to give an (arbitray) cost between pickups within a sector.           

    '''
    df = pd.Series(demand).to_frame()
    df.columns = ['demand']

    df = df.loc[df['demand'] > 1]
    if len(df) == 0:
        return demand, matrix

    #for each sectors with > 1 demand
    for row in range(df.shape[0]):
        #create n clone labels
        clone_memory = []
        original_label = df.iloc[row].name
        for i in range(df.iloc[row]['demand'] - 1):
            clone_label = f'{original_label}_{i+1}'
            clone_memory.append(clone_label)

            #clone and create series 
            clone_series = matrix[original_label].copy()
            clone_series.name = clone_label
            matrix[clone_label] = clone_series

            #clone and append row  (this doesn't append)
            clone_row = matrix[original_label].copy().T
            clone_row.index.name = clone_label
            clone_row.name = clone_label
            matrix = matrix.append(clone_row)

            #add single demand to dict
            demand[clone_label] = 1.0

            #intra postcode sector travel cost fudge
            if intra_sector_travel_cost > 0.0:
                matrix.iloc[-1][clone_label] = intra_sector_travel_cost
                matrix.iloc[-1][original_label] = intra_sector_travel_cost
                matrix.loc[original_label][clone_label] = intra_sector_travel_cost
                

                #add travel cost to clones in memory
                for other_clone in clone_memory:
                    matrix[other_clone][clone_label] = intra_sector_travel_cost
                    matrix[clone_label][clone_label] = intra_sector_travel_cost

            #now set original demand to 1.0
            demand[original_label] = 1.0

        return demand, matrix

def sort_cost_matrix_lexographically(matrix):     
    #sort columns
    sorted_cols = sorted(list(matrix.columns))
    #sort by index
    matrix = matrix[sorted_cols]
    return matrix.reindex(sorted_cols, axis=0)
    

     
class BruteForceRouteTuner(object):
    '''
    When routes are small < 6, there may be a small amount of benefit from a 
    final optimisation local optimisation of each route. 
    
    This class loops through each route (subtours) and enumerates all 
    combinations and selects the one with the lowest cost.  

    Could also be done quickly by an exact method for small problems.
    '''
    def __init__(self, vrp_solver, warehouse):
        self.vrp_solver = vrp_solver
        self.warehouse = warehouse


    def solve(self, vehicle_capacity, demand, matrix):
        vrp_solution = self.vrp_solver.solve(vehicle_capacity, 
                                             demand, 
                                             matrix)

        obj = SimpleTSPObjective(matrix.to_numpy())
        
        for route in vrp_solution:
            #1. convert to numpy array of numeric indexes
            tour = convert_route_to_tsp_tour(self.warehouse, 
                                             route, 
                                             matrix)
                                            
            #2. Brute force the combination of the middle 3-4 routes
            b_solver = BruteForceSolver(np.array(tour), obj)
            b_solver.solve()
            new_tour = b_solver.best_solutions[0]

            #3. overwrite the journey and convert back to str format
            route['route'] = convert_tsp_tour_to_route(new_tour, 
                                                       self.warehouse, 
                                                       matrix)

        #vrp solution with slightly tuned ordering of cities (potentially)
        return vrp_solution

def convert_route_to_tsp_tour(warehouse, route, matrix):
    '''
    tsp tour format = [0, 2, 3, 1] where 0 is base.
    '''
    cols = route['route'].split('-')
    warehouse_index = matrix.columns.get_loc(warehouse)
    tour = [matrix.columns.get_loc(c) for c in cols if c in matrix]
    tour.insert(0, warehouse_index)
    return tour

def convert_tsp_tour_to_route(tsp_tour, warehouse, matrix):
    tsp_tour = np.asarray(tsp_tour)
    warehouse_index = matrix.columns.get_loc(warehouse)
    pos_warehouse = np.where(tsp_tour == warehouse_index)[0][0]
    tsp_tour = np.append(tsp_tour[pos_warehouse:], tsp_tour[:pos_warehouse])

    route = ''
    for city_index in tsp_tour[1:]:
        route += matrix.columns[city_index] + '-'

    #remove last '-'
    return route[:-1]


class ILSWithConstructive(object):
    def __init__(self, constructive, warehouse, iterations):
        '''
        Parameters:
        --------
        constructive - object
            create initial solution via construction (e.g. CW savings)
        
        warehouse - str
            base

        iterations - int
            number of iterations for ILS
        '''
        self.constructive = constructive
        self.warehouse = warehouse
        self.iter = iterations

    def solve(self, vehicle_capacity, demand, matrix):
        '''
        Run the heuristic solver.

        Parameters:
        --------
        vehicle_capacity: int, 
            no. of seats per vehicle
        
        demand: dict
            demand by postcode sector

        matrix: pd.DataFrame
            cost matrix, distance or time

        Returns:
        -------
        dict
            routes
        '''
        init_solution = self.constructive.solve(vehicle_capacity, 
                                                demand, 
                                                matrix)   
        tour = []
        for route in init_solution:
            sub_tour = convert_route_to_tsp_tour(self.warehouse, route, matrix)
            tour.append(sub_tour[1:])

        tour = np.concatenate(tour)

        warehouse_index = matrix.columns.get_loc(self.warehouse)

        objective = CVRPUnitDemandObjective(matrix, 
                                            warehouse=warehouse_index, 
                                            capacity=vehicle_capacity)
        
        local_search = OrdinaryDecent2Opt(objective, tour)

        ils = IteratedLocalSearch(objective, 
                                  local_search,
                                  accept=EpsilonGreedyHomeBase(epsilon=0.2),
                                  maximisation=False)
        
        ils.run(self.iter)
        self.best_cost, solutions = ils.get_best_solutions()
        solution = solutions[0]
        self.solution = solutions
        journeys = []
        
        tour = self._convert_tour_to_routes(solution, vehicle_capacity)    
        for sub_tour in tour:
            route = self._convert_tsp_tour_to_route(sub_tour, matrix)
            route = {'route':route}
            route['demand'] = len(sub_tour)
            journeys.append(route)

        return journeys

    def _convert_tour_to_routes(self, tour, capacity):
        '''
        Easy as demand comes in single units and
        capacity is an integer
        '''
        n_cities = len(tour)
        splits = [i for i in range(capacity, n_cities, capacity)]
        routes = np.split(tour, splits)
        return routes


    def _convert_tsp_tour_to_route(self, tsp_tour, matrix):
        tsp_tour = np.asarray(tsp_tour)
        route = ''
        for city_index in tsp_tour:
            route += matrix.columns[city_index] + '-'

        #remove last '-'
        return route[:-1]


class MultipleReplicationRunner():
    def __init__(self, model, random_state=None):
        '''
        Parameters:
        -------
        model: TransportExperiment
            experiment to run multiple times.
        random_state: int
            set numpy random number seed
        '''
        self.model = model

        if not random_state is None:
            np.random.seed(random_state)

    def execute(self, n_reps=10, n_jobs=-1):
        '''
        Multiple independent replications of a model

        Parameters
        ----------
        n_reps : int, optional
            number of independent replications. The default is 10.
        n_jobs : int, optional
            No.of cores for parallel reps (-1 for all cores). The default is -1.

        Returns
        -------
        res : List
        '''
        costs = Parallel(n_jobs=n_jobs)(delayed(self.single_run)(self.model) 
                                        for _ in range(n_reps))
        return costs

    def single_run(self, model):
        '''
        Single replication of the simulation model.
        '''
        costs = model.single_replication()
        return costs


class ScenarioManager():
    '''
    Execute mulitple replicatins of multiple scenarios.
    '''
    def __init__(self, scenarios, solver, random_state=None):
        '''
        ScenarioManager

        Parameters:
        scenarios: dict (str:Scenario)
            scenarios to run

        solver: object
            The VRP solver object
        
        random_state: int optional (default = None)
            random seed.  When None runs are not reproducible.
        '''
        self.scenarios = scenarios
        self.solver = solver

        if not random_state is None:
            np.random.seed(random_state)
    
    def execute(self, n_reps=10, n_jobs=-1):
        '''
        Execute n_reps independent replications of each scenario

        Parameters:
        ---------
        n_reps: int optional (default=10)
            number of replications

        n_jobs:int optional (default=-1)
            no. processes to use -1 = all.

        Returns:
        -------
        dict
             a dict of pd.DataFrames
        '''
        scenario_results = {}

        for scenario_name, scenario in self.scenarios.items():
            model = TransportExperiment(scenario=scenario, solver=self.solver)
            runner = MultipleReplicationRunner(model=model)
            print(f'Running scenario: {scenario_name}...', end=' ')
            results = runner.execute(n_reps=n_reps, n_jobs=n_jobs)
            scenario_results[scenario_name] = pd.DataFrame(results)
            print('done.')

        print('All experiments completed.')
        return scenario_results