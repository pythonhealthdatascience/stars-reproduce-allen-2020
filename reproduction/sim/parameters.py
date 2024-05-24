'''
Contains classes for simulation model
'''
import numpy as np


class Normal:
    '''
    Wraps a normal distribution and its parameters.
    Allows lower truncation of normal distribution.
    Allows control of random number stream.
    '''

    def __init__(self, mean=0.0, std=1.0, minimum=None, random_seed=None):
        '''

        Constructor for Normal Distribution

        Parameters
        ----------
        mean : float, optional
            mean of the normal distribution. The default is 0.0
        std : float, optional
            stdev of the normal distribution. The default is 1.0
        minimum: float, optional
            lower truncation point of the normal dist. if None
            then distribution is not truncated.  Default is None.
        random_seed: int, optional (default=None)
            A random seed to reproduce samples.  If set to none then a unique
            sample is created.

        '''
        self.rng = np.random.default_rng(seed=random_seed)
        self.mean = mean
        self.std = std
        self.minimum = minimum

    def sample(self, size=None):
        '''
        Samples from the normal distribution with
        specified parameters.

        Lower truncates values if self.trunc is set.

        Parameters
        ----------
        size : int, optional
            Number of samples to return. The default is None.

        Returns
        -------
        scalar or numpy.array of
            normally distributed variates.

        '''
        sample = self.rng.normal(self.mean, self.std, size=size)

        if self.minimum is not None:
            if size is None:
                sample = max(sample, self.minimum)
            else:
                sample[sample < self.minimum] = self.minimum

        return sample


class Uniform:
    '''
    Wraps a uniform distribution and its parameters
    Allows control of random number stream.
    '''

    def __init__(self, minimum, maximum, random_seed=None):
        '''
        Constructor of the Uniform Distribution
        sampling object

        Parameters
        ----------
        minimum : float, optional
            Min of the uniform distribution. The default is 0.0.
        maximum : TYPE, optional
            Max of the uniform distribution. The default is 1.0.
        random_seed: int, optional (default=None)
            A random seed to reproduce samples. If set to none then a unique
            sample is created.
        '''
        self.rng = np.random.default_rng(seed=random_seed)
        self.maximum = maximum
        self.minimum = minimum

    def sample(self, size=None):
        '''
        Samples from the uniform distribution with
        specified parameters

        Parameters
        ----------
        size : int, optional
            Number of samples to return. The default is None.

        Returns
        -------
        scalar or numpy.array of
            uniform distributed variates.
        '''

        return self.rng.uniform(
            low=self.minimum, high=self.maximum, size=size)


DEFAULT_RUN_LENGTH = 200
DEFAULT_AUDIT_INTERVAL = 1
DEFAULT_PROPORTION_INFECTED = 0.8
DEFAULT_PROPORTION_NEG_COV_QUERY = 0.02
DEFAULT_MORTALITY = 0.15
DEFAULT_PROPORTION_POS_INPATIENT = 0.4
DEFAULT_RANDOM_POSITIVE = 0
DEFAULT_OPEN_ALL_SESSIONS = False
DEFAULT_DROP_TO_TWO_SESSIONS = False
DEFAULT_PROPORTION_DROP_TO_TWO = 0.9


class Scenario:
    '''
    Container class for DialysisSim parameters/arguments.
    Passed to the model and its process classes.
    '''
    def __init__(
            self,
            run_length=DEFAULT_RUN_LENGTH,
            audit_interval=DEFAULT_AUDIT_INTERVAL,
            total_proportion_people_infected=DEFAULT_PROPORTION_INFECTED,
            prop_neg_patients_cov_query=DEFAULT_PROPORTION_NEG_COV_QUERY,
            mortality=DEFAULT_MORTALITY,
            proportion_pos_requiring_inpatient=(
                DEFAULT_PROPORTION_POS_INPATIENT),
            random_positive_rate_at_start=DEFAULT_RANDOM_POSITIVE,
            open_all_sessions=DEFAULT_OPEN_ALL_SESSIONS,
            drop_to_two_sessions=DEFAULT_DROP_TO_TWO_SESSIONS,
            prop_patients_drop_to_two_sessions=DEFAULT_DROP_TO_TWO_SESSIONS):
        '''
        Create a scenario to with parameters for the simulation model

        Parameters:
        -----------
        TODO: Add these.
        '''
        # Parameters
        self.run_length = run_length
        self.audit_interval = audit_interval
        # Proportion of all people who will get infected (limited by herd
        # immunity) really this is init only...
        self.total_proportion_people_infected = (
            total_proportion_people_infected)
        # Proportion negative people who 'may' have COV
        self.prop_neg_patients_cov_query = prop_neg_patients_cov_query
        # Mortality rate
        self.mortality = mortality
        # Proportion Cov+ requiring inpatient care
        self.proportion_pos_requiring_inpatient = (
            proportion_pos_requiring_inpatient)
        # Add random positives at start; applies to negative patients
        self.random_positive_rate_at_start = random_positive_rate_at_start

        # Sampling (set up with no seed provided - can later rerun with a seed
        # via set_random_no_set())
        self.random_number_set = None
        self.init_sampling()

        # Strategies
        self.open_all_sessions = open_all_sessions
        self.drop_to_two_sessions = drop_to_two_sessions
        self.prop_patients_drop_to_two_sessions = (
            prop_patients_drop_to_two_sessions)

    def set_random_no_set(self, random_number_set):
        '''
        Controls the random sampling - can pass in a new random number set and
        do the sampling using that instead of the default.

        Parameters:
        ----------
        random_number_set: int
            Used to control the set of pseudorandom numbers
            used by the distributions in the simulation.
        '''
        # Replace the random_number_set
        self.random_number_set = random_number_set
        # Trigger recreation of sampling distributions
        self.init_sampling()

    def init_sampling(self):
        '''
        Create the distributions used by the model and initialise
        the random seeds of each.
        '''
        # Generate 20 high quality child seeds to use to create separate
        # independent random number generators for each distribution
        seeds = np.random.SeedSequence(self.random_number_set).spawn(20)

        # Infection distribution type (default = Normal)
        self.time_to_infection = Normal(60, 15, 0.0, random_seed=seeds[0])

        # Sampling distribution for time positive
        self.time_positive = Uniform(7, 14, random_seed=seeds[1])

        # Proportion Cov+ requiring inpatient care
        self.requiring_inpatient_random = Uniform(
            0.0, 1.0, random_seed=seeds[2])
        self.time_pos_before_inpatient = Uniform(3, 7, random_seed=seeds[3])
        self.time_inpatient = Uniform(7.0, 14.0, random_seed=seeds[4])

        # Mortality random number
        self.mortality_rand = Uniform(0.0, 1.0, random_seed=seeds[5])

        # Restrict the maximum proportion of people who can be infected
        self.will_be_infected_rand = Uniform(0.0, 1.0, random_seed=seeds[6])
