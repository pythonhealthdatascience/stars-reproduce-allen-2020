import simpy
import pandas as pd
import numpy as np

from sim.patient import Patient
from sim.units import Dialysis_units
from sim.allocation import AllocatePatients
from sim.audit import Audit

class Population:
    """
    
    Population class which holds dictionary and lists of patients.
    
    
    Attributes
    ----------
    
    patients: dictionary of all patients
    unallocated_patients: list (of patient objects) of patients not currently allocated
    displaced_patients: list (of patient objects) of patients displaced from home unit
    negative_patients: list (of patient objects) of COVID positive patients
    positive_patients: list (of patient objects) of COVID negative patients
    recovered_patients: list (of patient objects) of recovered COVID patients
    died_patients: list (of patient objects) of died COVID patients
    default_travel_times: list of current travel times for each patient
    inpatients: list (of patient objects) of inpatients
        
    """
    
    def __init__(self):
        """
        Constructor method for population
        """
        
        # Patient populations
        self.patients = dict()
        self.unallocated_patients = []
        self.displaced_patients = []
        self.negative_patients = []
        self.positive_patients = []
        self.recovered_patients = []
        self.died_patients = []
        self.default_travel_times = []
        self.inpatients = [] 
        

class DialysisSim:
    """
    Simulation model class.
    
    Attributes
    ----------
    
    _params: Scenario parameters
    _env: SimPy environment
    _units: Reference to dialysis units object
    allocate: Patient allocation object
    audit: Audit object (patients, units, displaced patients, inpatients)
    patient_data: patient data (location and current unit) read from CSV
    
    
    Methods
    -------
    
    check_sessions_for_unallocated_patients:
        If there are patients unallocated to sessions, check (daily) whether they can be
        allocated (as room in sessions is made free by other patients being reallocated as
        COVID status changes.)
        
    reallocate_all_patients:
        Reallocation of all patients reassigns all patients, optimising use of units and minimising
        travel times for patients. Is called typically every 7 days.
        
    run:
        Set up regular processes (audits + reallocation methods). And start environment running.
    
    set_up_patient_population:
        Create patient objects, and start virus progression for each patient.
        
    
    """    
    
    
    def __init__(self, scenario):
        """constructor for initiating simpy simulation environment"""
        
        self._params = scenario

        # Set up simpy environment        
        self._env = simpy.Environment()
        # Set up units
        self._units = Dialysis_units(self._env)
        # Set up population 
        self.pop = Population()
        # Set up patient/unit allocations methods
        self.allocate = AllocatePatients(self._units, self._params, self.pop)
        # Set up audit class
        self.audit = Audit(self._env, self.allocate, self.pop, self._params, self._units.unit_info)
        
        # Load patient data:
        self.patient_data = pd.read_csv('sim/patients.csv')
        self.patient_data['COVID status'].fillna('negative', inplace=True)
        
        # Initiate patient population
        self.set_up_patient_population()
        
    def check_sessions_for_unallocated_patients(self):
        """
        If there are patients unallocated to sessions, check (daily) whether they can be
        allocated (as room in sessions is made free by other patients being reallocated as
        COVID status changes.)
        """
        
        while True:
            # Check if there are unallocated patients
            if len(self.pop.unallocated_patients) > 0:
                
                # First compress allocated cov +ve sessions
                for patient in self.pop.positive_patients:
                    if patient.unallocated_to_session == False:
                        self.allocate.units_count.loc[patient.current_unit][patient.session] -= 1
                        # Check if session can be re-allocated
                        if self.allocate.units_count.loc[patient.current_unit][
                            patient.session] == 0:
                            self.allocate.units.loc[patient.current_unit][patient.session] = 'neg'
                
                # Re-assign cov +ve patients
                print('reassigning patients')
                for patient in self.pop.positive_patients:
                    if patient.unallocated_to_session == False:
                        self.allocate.allocate_patient(patient)
                
                # Now go through unallocated patient list
                still_unallocated = []
                # Use dictionary to skip reallocation when no more neg or pos can be reallocated
                re_allocate = {'negative': True, 'positive': True, 'recovered': True}
                # Go through unallocated patient list, remove and try to allocate
                while len(self.pop.unallocated_patients) > 0:
                    # Remove patient from unallocated list
                    patient = self.pop.unallocated_patients.pop()
                    # Check dictionary whether COVID class can be re-allocated
                    if re_allocate[patient.status]:
                        # Allocat epatient to session
                        self.allocate.allocate_patient(patient) 
                        # Check if patient has been re-allocated
                        if patient.unallocated_to_session:
                            # Not possible to allocate, set dictionary to avoid same status again
                            re_allocate[patient.status] = False
                            still_unallocated.append(patient)
                    # If reallocation skipped, add directly to new list of unallocated patients        
                    else:
                        still_unallocated.append(patient)
                        
                # Refresh list of unalocated population in opo class
                self.pop.unallocated_patients = still_unallocated
                
            # Delay of 1 day befor enext reallocation 
            yield self._env.timeout(1)
            
            
    def reallocate_all_patients(self):
        """
        Reallocation of all patients reassigns all patients, optimising use of units and minimising
        travel times for patients. Is called typically every 28 days.

        """
        
        # Set up dictionary to hold population lists by COVID status
        patient_dict = {'negative': self.pop.negative_patients, 
                        'positive': self.pop.positive_patients,
                        'recovered': self.pop.recovered_patients}
        
        # Continuous loop
        while True:
            
            # Delay before first reallocation
            yield self._env.timeout(7.1)
             
            # Run reallocation only if patients currently displaced from their home unit
            if len(self.pop.displaced_patients) > 0:
                
                # Remove all patients from population lists
                for key, patient in self.pop.patients.items():
                    # Do not reallocate inpatients and died patients
                    if patient.status in ['negative', 'positive', 'recovered']:
                        self.allocate.remove_patient(patient)
                        # Add patient to temprary lists of patients
                        patient_dict[patient.status].append(patient)  
                
                # Reset list of displaced patients
                self.pop.displaced_patients = []
                
                # Allocate patients (Cov +ve first then negative)
                if len(self.pop.positive_patients) > 0:
                    for patient in self.pop.positive_patients:
                        self.allocate.allocate_patient(patient)
                if len(self.pop.recovered_patients) > 0:
                    for patient in self.pop.recovered_patients:
                        self.allocate.allocate_patient(patient)
                if len(self.pop.negative_patients) > 0:
                    for patient in self.pop.negative_patients:
                        self.allocate.allocate_patient(patient)

            # Wait 28 days to next reallocation
            yield self._env.timeout(7)
            
            
    def run(self):
        """
        Set up regular processes (audits + reallocation methods). And start environment running.
        """
        
        # Initialise processes that will run on model run
        self._env.process(self.audit.perform_patient_audit())
        self._env.process(self.audit.perform_unit_level_audit())
        self._env.process(self.check_sessions_for_unallocated_patients())
        self._env.process(self.reallocate_all_patients())

        # Run
        self._env.run(until=self._params.run_length)

            
    
    def set_up_patient_population(self):
        """
        Create patient objects, and start virus progression for each patient.
        """

        # Instantise patients
        for key, value in self.patient_data.iterrows():

        # Set up patient details in dictionary (to be passed to Patient class)
            patient_dict = dict()
            patient_dict['patient_id'] = value['Patient ID']
            patient_dict['location'] = value['Postcode sector']
            patient_dict['dialysis_type'] = value['Patient type']
            patient_dict['first_day'] = value['first_day']
                        
            patient_dict['will_be_infected'] = (
                True if self._params.will_be_infected_rand.sample() < 
                self._params.total_proportion_people_infected else False)

            patient_dict['time_to_infection'] = (
                    self._params.time_to_infection.sample() if 
                    patient_dict['will_be_infected'] else 99999)

            patient_dict['time_positive'] = self._params.time_positive.sample()
            patient_dict['status'] = value['COVID status']
            
            # Turn all current suspected into negatives (assume will be treated in side rooms)
            if patient_dict['status'] == 'suspected':
                patient_dict['status'] = 'negative'
                
            # Set default unit location
            patient_dict['default_unit_location'] = value['Site Postcode']
                
            # Get subunits for default unit
            if patient_dict['default_unit_location'] == 'HOME':
                patient_dict['default_unit'] = ['HOME']
            else:
                master_unit = value['Site']
                subunits = list(self._units.unit_info[
                    self._units.unit_info['unit']==master_unit].index)
                patient_dict['default_unit'] = subunits
                
            # Set inpatient-related parameters
            patient_dict['require_inpatient'] = (
                True if self._params.requiring_inpatient_random.sample() < 
                self._params.proportion_pos_requiring_inpatient else False)
            if patient_dict['require_inpatient']:
                # Over-write pos LoS (as used for outpatient care)
                patient_dict['time_positive'] = self._params.time_pos_before_inpatient.sample()
                patient_dict['inpatient_los'] = self._params.time_inpatient.sample()
            else:
                patient_dict['inpatient_los'] = 0

            # Create patient and add to patient population
            patient = Patient(
                self._env, patient_dict, self.allocate, self._params, self.pop, self._units)
            self.pop.patients[value['Patient ID']] = patient
            
            # Allocate patient to unit
            self.allocate.load_patient(patient)
            
            # Add default travel time to Population list
            self.pop.default_travel_times.append(patient.default_time)
            
            # Start patient virus progression
            self._env.process(patient.patient_virus_progress())