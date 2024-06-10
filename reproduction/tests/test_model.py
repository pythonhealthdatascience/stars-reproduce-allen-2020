'''
Model testing

This module contains tests to confirm whether the simulation model is
producing consistent results.
'''

import pytest
import pandas as pd
# import sim.sim_replicate as sim
# from sim.parameters import Scenario
from pathlib import Path

'''
def run_model():
    # Run model with parameters from computational reproducibility assessment
    scenarios = {}
    scenarios['base_3_month'] = Scenario(
        run_length=150,
        proportion_pos_requiring_inpatient=0.6)
    number_of_replications = 30
    base_random_set = 2700
    output_folder = 'test_output'
    sim.run_replications(
        scenarios, number_of_replications, base_random_set, output_folder)
'''

# TO DO: Try removing the init files and see if it works still
# TO DO: Correct test path to test folder
# Paths to expected and test outputs from the model
DISPLACED = 'base_3_month_reps_30_displaced_audit.csv'
INPATIENT = 'base_3_month_reps_30_inpatient_audit.csv'
PATIENT = 'base_3_month_reps_30_patient_audit.csv'
UNIT = 'base_3_month_reps_30_unit_audit.csv'
EXP_FOLDER = 'data'
TEST_FOLDER = 'data'

# Create empty list to populate with tuples of paths to test and expected files
paths = []
for file in [DISPLACED, INPATIENT, PATIENT, UNIT]:
    test_path = Path(__file__).parent.joinpath(TEST_FOLDER, file)
    exp_path = Path(__file__).parent.joinpath(EXP_FOLDER, file)
    paths.append((test_path, exp_path))


# Repeat function on each of the tuples in `paths`
@pytest.mark.parametrize('test_df, expected_df', paths)
def test_equal_df(test_df, expected_df):
    '''
    Test that results are consistent with the expected results (which are
    from the computational reproducibility assessment)
    '''
    test_result = pd.read_csv(test_df)
    expected_result = pd.read_csv(expected_df)
    pd.testing.assert_frame_equal(test_result, expected_result)
