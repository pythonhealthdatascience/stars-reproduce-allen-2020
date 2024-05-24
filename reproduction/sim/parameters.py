'''
Contains data classes for simulation model
'''
from dataclasses import dataclass
import numpy as np


class Normal():
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


class Uniform():
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


@dataclass(frozen=True)
class Scenario:
    '''
    Dataclass for DialysisSim

    Encapsulates all parameters for the simulation model.  

    Note the @dataclass decorator.  This takes
    a parameter call frozen which means the class
    is immutable.  That's nice for parameters!
    '''

    # Generate N_STREAMS high quality child seeds
    default_seed = 42
    n_streams = 20
    seed_sequence = np.random.SeedSequence(default_seed)
    seeds = seed_sequence.spawn(n_streams)

    run_length: float = 200

    audit_interval: int = 1

    # Proportion of all people who will get infected (limited by herd immunity)
    # really this is init only...
    total_proportion_people_infected: float = 0.8

    # Proportion negative people who 'may' have COV
    prop_neg_patients_cov_query: float = 0.02

    # Infection distribution type (default = Normal)
    time_to_infection = Normal(60, 15, 0.0, random_seed=seeds[0])

    # Sampling distribution for time positive
    time_positive = Uniform(7, 14, random_seed=seeds[1])

    # Proportion Cov+ requiring inpatient care
    proportion_pos_requiring_inpatient: float = 0.4
    requiring_inpatient_random = Uniform(0.0, 1.0, random_seed=seeds[2])
    time_pos_before_inpatient = Uniform(3, 7, random_seed=seeds[3])
    time_inpatient = Uniform(7.0, 14.0, random_seed=seeds[4])

    # Mortality rate
    mortality: float = 0.15

    # Mortality random number
    mortality_rand = Uniform(0.0, 1.0, random_seed=seeds[5])

    # Add random positives at start; applies to negative patients
    random_positive_rate_at_start: float = 0.0

    # Restrict the maximum proportion of people who can be infected
    will_be_infected_rand = Uniform(0.0, 1.0, random_seed=seeds[6])

    # Strategies ---------------------------------

    open_all_sessions: bool = False
    drop_to_two_sessions: bool = False
    prop_patients_drop_to_two_sessions: float = 0.9
