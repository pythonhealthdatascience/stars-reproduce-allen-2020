import sim.sim_replicate as sim
from sim.parameters import Scenario
import tempfile


def pytest_configure(config):
    '''
    Performs initial configuration - runs the simulation model with parameters
    from computational reproducibility assessment and saves results in
    temporary directory
    '''
    scenarios = {}
    scenarios['base_3_month'] = Scenario(
        run_length=150,
        proportion_pos_requiring_inpatient=0.6)
    number_of_replications = 30
    base_random_set = 2700
    config.test_folder = tempfile.mkdtemp()
    sim.run_replications(
        scenarios,
        number_of_replications,
        base_random_set,
        config.test_folder,
        plot=False)
