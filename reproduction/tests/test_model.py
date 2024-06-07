'''
Model testing

This module contains tests to confirm whether the simulation model is
producing consistent results.
'''

import pytest
import pandas as pd
import sim.sim_replicate as sim
from sim.parameters import Scenario
from pathlib import Path

DISPLACED = 'base_3_month_reps_30_displaced_audit.csv'
PATH_DISPLACED_1 = Path(__file__).parent.joinpath('data', DISPLACED)
PATH_DISPLACED_2 = Path(__file__).parent.joinpath('data', DISPLACED)

@pytest.mark.parametrize(
    'displaced_audit',
    [
        (PATH_DISPLACED_1),
        (PATH_DISPLACED_2),
    ],
)

def run_model():
    '''
    Run model with parameters from computational reproducibility assessment
    '''
    scenarios = {}
    scenarios['base_3_month'] = Scenario(
        run_length=150,
        proportion_pos_requiring_inpatient=0.6)
    number_of_replications = 30
    base_random_set = 2700
    output_folder='test_output'
    sim.run_replications(
        scenarios, number_of_replications, base_random_set, output_folder)

#def test_displaced(displaced_audit):
#    '''
#    Test that results are consistent with those from the computational
#    reproducibility assessment
#    '''
#    displaced_data = pd.read_csv(displaced_audit)

'''
# Import model
import sim.sim_replicate as sim
from sim.parameters import Scenario

def test_reproduction():
    # Test run model as set-up for computational reproducibility assessment.
    # Parameters
    scenarios = {}
    scenarios['base_3_month'] = Scenario(
        run_length=150,
        proportion_pos_requiring_inpatient=0.6)
    number_of_replications = 30
    base_random_set = 2700
    output_folder='test_output'

    # Import expected results
    displaced = pd.read_csv('data/base_3_month_reps_30_displaced_audit.csv')
    inpatient = pd.read_csv('data/base_3_month_reps_30_inpatient_audit.csv')
    patient = pd.read_csv('data/base_3_month_reps_30_patient_audit.csv')
    unit = pd.read_csv('data/base_3_month_reps_30_unit_audit.csv')

    # Run the simulation
    sim.run_replications(
        scenarios, number_of_replications, base_random_set, output_folder)

    # Import the test results
    test_displaced = pd.read_csv('test_output/base_3_month_reps_30_displaced_audit.csv')

    # Compare against actual results
    assert pd.testing.assert_frame_equal(displaced, test_displaced)
'''