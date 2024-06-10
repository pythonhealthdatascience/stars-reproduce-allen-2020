'''
Model testing

This module contains tests to confirm whether the simulation model is
producing consistent results.
'''

import pytest
import pandas as pd
from pathlib import Path


# Filenames for each of the results to be compared, and folder of containing
# expected results.
DISPLACED = 'base_3_month_reps_30_displaced_audit.csv'
INPATIENT = 'base_3_month_reps_30_inpatient_audit.csv'
PATIENT = 'base_3_month_reps_30_patient_audit.csv'
UNIT = 'base_3_month_reps_30_unit_audit.csv'


# Name of folder containing expected results
@pytest.fixture
def exp_folder():
    return 'exp_results'


# Run this function as separate tests on each of the files
@pytest.mark.parametrize('file', [DISPLACED, INPATIENT, PATIENT, UNIT])
def test_equal_df(file, exp_folder, request):
    '''
    Test that results are consistent with the expected results (which are
    from the computational reproducibility assessment)
    '''
    # Import test and expected results
    # test_result = pd.read_csv(temp_dir.join(file))
    test_result = pd.read_csv(Path(__file__).parent.joinpath(
        request.config.test_folder, file))
    exp_result = pd.read_csv(Path(__file__).parent.joinpath(exp_folder, file))

    # Check that the dataframes are equal
    pd.testing.assert_frame_equal(test_result, exp_result)
