import pandas as pd
import numpy as np

from joblib import Parallel, delayed

import vrp.io as io
import vrp.constructive as c
import vrp.sim as sim
from vrp.constructive import SequentialClarkeWright
from vrp.sim import ILSWithConstructive

def multiple_replications(scenario, n_reps=10, n_jobs=1):
    '''
    Multiple independent replications of DialysisSim for a 
    scenario

    Parameters
    ----------
    scenario : dataclass Scenario
        parameters for the scenario.
    n_reps : int, optional
        number of independent replications. The default is 10.
    n_jobs : int, optional
        No.of cores for parallel reps (-1 for all cores). The default is 1.

    Returns
    -------
    res : List
    '''
    
    costs = Parallel(n_jobs=n_jobs)(delayed(single_run)(scenario, i) 
                                     for i in range(n_reps))
    return costs

def single_run(scenario, i=0):
    '''
    Single replication of the simulation model.
    '''
    #heuristic procedure that creates routes
    cw = SequentialClarkeWright(WAREHOUSE, 
                                c.adjacent_route_tail,
                                c.merge_tail)
                              
    if MODE == 'CW':
        solver = cw
    elif MODE == 'ILS':
        solver = ILSWithConstructive(cw, WAREHOUSE, iterations=ILS_ITER)  
    elif MODE == 'BRUTE':
        solver = sim.BruteForceRouteTuner(vrp_solver=cw,
                                          warehouse=WAREHOUSE)
    model = sim.TransportExperiment(scenario, solver) 
    costs = model.single_replication()
    return costs

if __name__ == '__main__':
    
    #location of warehouse/depot
    WAREHOUSE = 'L51'
    #No. of Iterated Local Search Iterations
    ILS_ITER = 20

    #no. of independent repliations 
    N_REPS = 1000
    #-1 for parallel replications; 1 for single; 2 for 2 etc.
    N_JOBS = -1 

    #MODE: 'CW', 'BRUTE', 'ILS'
    MODE = 'ILS'

    #random number seed for reproducible runs
    SEED = 999
    np.random.seed(seed=SEED)

    #load travel time matrix
    full_matrix = io.load_travel_time()
    postcode_counts = io.load_patient_postcode_count()
    postcode_distribution = sim.create_postcode_distribution(postcode_counts)
    
    #sim parameters
    scenario_20 = sim.Scenario(n_patients=20,
                               warehouse=WAREHOUSE,
                               vehicle_capacities=[2, 3, 4],
                               cost_matrix = full_matrix,
                               postcode_distribution=postcode_distribution,
                               p_positive=1.0, 
                               p_transport=1.0)

    scenario_30 = sim.Scenario(n_patients=30,
                               warehouse=WAREHOUSE,
                               vehicle_capacities=[2, 3, 4],
                               cost_matrix = full_matrix,
                               postcode_distribution=postcode_distribution,
                               p_positive=1.0, 
                               p_transport=1.0)

    scenario_40 = sim.Scenario(n_patients=40,
                               warehouse=WAREHOUSE,
                               vehicle_capacities=[2, 3, 4],
                               cost_matrix = full_matrix,
                               postcode_distribution=postcode_distribution,
                               p_positive=1,
                               p_transport=1.0)

    scenario_60 = sim.Scenario(n_patients=60,
                               warehouse=WAREHOUSE,
                               vehicle_capacities=[2, 3, 4],
                               cost_matrix = full_matrix,
                               postcode_distribution=postcode_distribution,
                               p_positive=1.0, 
                               p_transport=1.0)

    scenarios = {}
    scenarios['20_positive'] = scenario_20
    scenarios['40_positive'] = scenario_40
    scenarios['60_positive'] = scenario_60

    scenario_results = {}
    for scenario_name, scenario in scenarios.items():
        print(f'Running scenario: {scenario_name}...', end=' ')
        results = multiple_replications(scenario, n_reps=N_REPS, n_jobs=N_JOBS)
        #results = single_run(scenario)
        file_name = f'vrp/output/{scenario_name}_{MODE}.csv'
        pd.DataFrame(results).to_csv(file_name)
        print('done.')

    print('All experiments completed.')



    



    