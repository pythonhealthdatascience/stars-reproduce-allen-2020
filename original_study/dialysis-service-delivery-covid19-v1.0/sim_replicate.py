from sim.end_trial_analysis import EndTrialAnalysis
from sim.helper_functions import expand_multi_index
from sim.model import DialysisSim
from sim.parameters import Scenario, Uniform, Normal
from joblib import Parallel, delayed
import pandas as pd


def run_replications(scenarios, number_of_replications=30):
    """
    Main simulation code. Calls multiple runs of prescribed sceanrios.
    
    Overview:
        
    * Prescribe number of runs per sceanrio
    * Define scenarios (as dictionary items)
    * Get audits from each scenario:
        * p_audits: count of all patients in different stages of COVID
        * u_audits: counts of patients (by COVID stage) at each unit
        * p_audits: count of displaced patients, and additional travel time
        * i_audits: count of inpatients
    * Expand audits (remove multi-index used to collate audits)
    * Save audits to csv files
    * Pass audits to end-run analysis

    Runs scenarios in separate threads using joblib
    
    Returns
    -------
    None.

    """
    
    # Number of runs per sceanrio
    N_REPS = number_of_replications
    
    # Add scenarios to be run to dictionary
    scenarios = scenarios

   
    # Loop through all scenarios
    for name, scenario in scenarios.items():
        
        print(f'Running {N_REPS} reps of {name} =>', end=' ')
        # Get audits from each sceanrio

        # Run each sceanrio in separate CPU thread (limit threads with n_jobs) 
        p_audits, u_audits, d_audits, i_audits = \
            multiple_replications(scenarios[name], n_reps=N_REPS, n_jobs=-1)
        
        # Expand multi-index to save as CSV
        p_audits = expand_multi_index(p_audits, ['scenario', 'day'])
        d_audits = expand_multi_index(d_audits, ['scenario', 'day'])
        u_audits = expand_multi_index(u_audits, ['scenario', 'audit#'])
        i_audits = expand_multi_index(i_audits, ['scenario', 'audit#'])

        # Save as CSV
        p_audits.to_csv(f'output/{name}_reps_{N_REPS}_patient_audit.csv', index=False)
        u_audits.to_csv(f'output/{name}_reps_{N_REPS}_unit_audit.csv', index=False)
        d_audits.to_csv(f'output/{name}_reps_{N_REPS}_displaced_audit.csv', index=False)
        i_audits.to_csv(f'output/{name}_reps_{N_REPS}_inpatient_audit.csv', index=False)

        # Run analysis after all replicate runs in a sceanrio
        analysis = EndTrialAnalysis(name, p_audits, u_audits, d_audits, i_audits)
        analysis.plot_patient_audit()
        analysis.plot_displaced_audit() 
        analysis.plot_unit_audit()
        
        print('Done.')



    # All sceanrios complete        
    


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
        List of Tuples (1 for each replication)
            0: Patient Audit.
            1. Unit Audit
    
    TM Note: At the moment this is not combined....

    '''
    
    audits = Parallel(n_jobs=n_jobs)(delayed(single_run)(scenario, i) 
                                     for i in range(n_reps))
    
    return unpack_audits(audits)

    
def single_run(scenario, i=0):
    '''
    Single run of DialySim for scenario
    
    Parameters
    ----------
    scenario : dataclass Scenario
        Parameters for model run.
    i : int, optional
        Replication number (0 if just single run). The default is 0.

    Returns
    -------
    pandas.DataFrame
        Patient Audit.
    pandas.DataFrame
        Unit Audit.

    '''
    print(f'{i}, ', end='' )
    model = DialysisSim(scenario)
    model.run()
    # return audits
    return model.audit.patient_audit, model.audit.unit_audit, \
        model.audit.displaced_audit, model.audit.inpatient_audit
            


def unpack_audits(audits):
    '''
    Unpacks the tuple returned from multiple reps into seperate multi-index 
    data frames.
    
    Returns a tuple with 2 dataframes.  These are multi-index dataframes.
    (rep, day).  E,g, if run length is 360 days and there are two replications
    there there are 720 rows.  360 have a first index column = 0; and the 
    second 360 have first index column = 1.
     
    Parameters
    ----------
    audits : Tuple
        Patient and unit audits from each rep.

    Returns
    -------
    patient_audits : DataFrame
        DataFrame of patient audits with multi-index (rep, day)
    unit_audits : List
        DataFrame of unit audits with multi-index (rep, day)

    '''
    
    # Set up lists for seperate model ausits
    patient_audits = []
    unit_audits = []
    displaced_audits = []
    inpatient_audits = []
    
    # Loop through model reps
    for i in range(len(audits)):
        patient_audits.append(audits[i][0])
        unit_audits.append(audits[i][1])
        displaced_audits.append(audits[i][2])
        inpatient_audits.append(audits[i][3])
    
    #convert to multi-index DF
    df_patient = pd.concat(patient_audits, 
                           keys=[i for i in range(len(audits))])
    df_unit = pd.concat(unit_audits, keys=[i for i in range(len(audits))])
    
    df_displaced = pd.concat(displaced_audits, keys=[i for i in range(len(audits))])
    df_inpatients = pd.concat(inpatient_audits, keys=[i for i in range(len(audits))])
    
    # Remove duplicate 'day'
    df_patient.drop('day', axis=1, inplace=True)
    df_displaced.drop('day', axis=1, inplace=True)
    
    # Return patient, unit, displaced patients, and inpatient audits
    return df_patient, df_unit, df_displaced, df_inpatients



if __name__ == '__main__':

    # Example run
    scenarios = {}
    
    # Base scenario
    scenarios['base_3_month'] = Scenario(
        run_length=150,
        total_proportion_people_infected = 0.8,
        time_to_infection = Normal(60, 15, 0.0),
        time_positive = Uniform(7, 14),
        proportion_pos_requiring_inpatient= 0.6,
        time_pos_before_inpatient = Uniform(3,7),
        time_inpatient = Uniform(7.0, 14.0),
        mortality = 0.15,
        random_positive_rate_at_start = 0.0
        )
        
    scenarios['base_4_month'] = Scenario(
        run_length=200,
        total_proportion_people_infected = 0.8,
        time_to_infection = Normal(80, 20, 0.0),
        time_positive = Uniform(7, 14),
        proportion_pos_requiring_inpatient= 0.6,
        time_pos_before_inpatient = Uniform(3,7),
        time_inpatient = Uniform(7.0, 14.0),
        mortality = 0.15,
        random_positive_rate_at_start = 0.0
        )
        
    number_of_replications = 30
    run_replications(scenarios, number_of_replications)


        
      

