import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class Audit:
    """
    Runs audit on patient and unit metrics at day intervals. Stores audits in DataFrames.
    
    Object attributes
    -----------------
    
    Audits stored are:
        displaced_audit: count of displaced patients, and additional travel time
        inpatient_audit: count of inpatients
        patient_audit: count of all patients in different stages of COVID
        unit_audit: counts of patients (by COVID stage) at each subunit
        
    Other class parameters:
        _allocate: reference to model patient-unit allocation object
        _env: Reference to model environment object
        _params: Reference to sceanrio paramters object
        _pop: Reference to model patient population object
        audit_subunit_list: : List of subunits to audit (for unit and inpatient audits)
        audit_unit_list: List of units to audit (for unit and inpatient audits)
        unit_info: Info on units
        
    Methods
    -------
    
    perform_patient_audit:
        Patient audits for patient counts and metrics on displaced patients
        Counts total patients in each COVID stage, the total number of patients,
        and the number of patients not allocated to any session
    
    perform_unit_level_audit:
        Unit level audits for outatients and inpatients.
        Counts the number of patients, by COVID stage, allocated to each unit.
        Also counts number ofCOVID postive/negative sessions at each unit.
        Provides both unit (master unit) and subunit.
    

    """    
    
    def __init__(self, env, allocate, pop, params, unit_info):
        """
        Constructor for audits and analysis
        
        Parameters
        ----------
        
        allocate: Object
            Model patient-unit allocation object
        env : Object
            Model enviornment object.
        params : Object
            Sceanrio paramaters object.
        pop : Object
            Object holding patient populations (all patients, patients by COVID
            stage, inpatients).
        unit_info : DataFrame
            Information on units
        
        Returns
        -------
        None.       
        
        """
        
        # Set up references to other model objects
        self._env = env
        self._allocate = allocate
        self._pop = pop
        self._params = params
        
        # Set up unit information (and add 'HOME' as a possible patient location)
        self.unit_info = unit_info
        self.audit_unit_list =list(unit_info['unit']) + ['HOME']
        self.audit_subunit_list =list(unit_info['subunit']) + ['HOME']
        self.unit_info.set_index('subunit', inplace=True)
        
        # Set up audit DataFrames
        self.patient_cols = [
            'day', 'negative', 'positive', 'recovered', 'inpatient', 'died', 'total', 'unallocated']
        self.patient_audit = pd.DataFrame(columns=self.patient_cols)

        self.displaced_cols = ['day', 'number', 'add_time_min', 'add_time_1Q', 'add_time_median', 
                                'add_time_3Q', 'add_time_max', 'add_time_total']
        self.displaced_audit = pd.DataFrame(columns=self.displaced_cols) 

        self.unit_cols = [
            'day', 'master_unit', 'subunit', 'negative', 'positive', 'recovered', 'neg+rec', 
            'total', 'negative_shifts', 'positive_shifts']
        self.unit_audit = pd.DataFrame(columns=self.unit_cols)
        
        self.inpatient_cols = ['day', 'master_unit', 'subunit', 'inpatients']
        self.inpatient_audit =  pd.DataFrame(columns=self.inpatient_cols)
        

    def perform_patient_audit(self):
        """
        Patient audits for patient counts and metrics on displaced patients
        Counts total patients in each COVID stage, the total number of patients,
        and the number of patients not allocated to any session"""
        
        # Continuous audit
        while True:
            
            # General patient audit (put audit results in dictionary and add to audit DataFrame)
            audit = dict()
            audit['day'] = self._env.now
            audit['negative'] = len(self._pop.negative_patients)
            audit['positive'] = len(self._pop.positive_patients)
            audit['recovered'] = len(self._pop.recovered_patients)
            audit['inpatient'] = len(self._pop.inpatients)
            audit['died'] = len(self._pop.died_patients)
            audit['total'] = len(self._pop.patients)
            audit['unallocated'] = len(self._pop.unallocated_patients)
            # Add dictionary to existing DataFrame
            self.patient_audit = \
                self.patient_audit.append(audit, ignore_index=True)
            
            # Displaced patient audit (put audit results in dictionary and add to audit DataFrame)
            audit = dict()
            # Get displaced times
            additional_time = []
            for patient in self._pop.displaced_patients:
                additional_time.append(patient.displaced_additional_time)
            audit['day'] = self._env.now
            audit['number'] = len(self._pop.displaced_patients)
            if len(additional_time) > 0:
                # Dispalced patients exist, calculate statistics
                audit['add_time_min'] = np.min(additional_time)
                audit['add_time_1Q'] = np.quantile(additional_time, 0.25)
                audit['add_time_median'] = np.quantile(additional_time, 0.50)
                audit['add_time_3Q'] = np.quantile(additional_time, 0.75)
                audit['add_time_max'] = np.max(additional_time)
                audit['add_time_total'] = np.sum(additional_time)
            else:
                # No displaced patients exist, set all statistics to zero
                audit['add_time_min'] = 0
                audit['add_time_1Q'] = 0
                audit['add_time_median'] = 0
                audit['add_time_3Q'] = 0
                audit['add_time_max'] = 0
                audit['add_time_total'] = 0
            # Add dictionary to existing DataFrame
            self.displaced_audit = \
                self.displaced_audit.append(audit, ignore_index=True)
            
            # Trigger next audit after interval
            yield self._env.timeout(self._params.audit_interval)
            
    def perform_unit_level_audit(self):
        """
        Unit level audit: Counts the number of patients, by COVID stage, allocated to each unit.
        Also counts number ofCOVID postive/negative sessions at each unit. 
        Provides both unit (master unit) and subunit.
        """

        # Continuous audit
        while True:

            audit = pd.DataFrame(columns=self.unit_cols)
      
            # Outpatient audit

            audit['negative'] = self._allocate.unit_sessions_count[
                self._allocate.unit_sessions == 'negative'].sum(axis=1)
            audit['positive'] = self._allocate.unit_sessions_count[
                self._allocate.unit_sessions == 'positive'].sum(axis=1)
            audit['recovered'] = self._allocate.unit_sessions_count[
                self._allocate.unit_sessions == 'recovered'].sum(axis=1)
            audit['neg+rec'] =  audit['negative'] + audit['recovered']
            audit['total'] = audit['negative'] + audit['positive'] + audit['recovered']
            audit['negative_shifts'] = (self._allocate.unit_sessions == 'negative').sum(axis=1)
            audit['positive_shifts'] = (self._allocate.unit_sessions == 'positive').sum(axis=1)
            audit['day'] = self._env.now
            audit['master_unit'] = self.audit_unit_list
            audit['subunit'] = self.audit_subunit_list
            audit.reset_index(inplace=True)
            audit.drop('index', axis=1, inplace=True)
            
            # Adjust patient counts if 2x weekly
            if self._params.drop_to_two_sessions:
                cols_to_adjust = ['negative', 'positive', 'recovered', 'neg+rec', 'total']
                audit[cols_to_adjust] = np.ceil(
                    (audit[cols_to_adjust] * 0.667 * 
                     self._params.prop_patients_drop_to_two_sessions) +
                     audit[cols_to_adjust] * (1 - self._params.prop_patients_drop_to_two_sessions))

            # Add audit to existing DataFrame            
            self.unit_audit = self.unit_audit.append(audit, ignore_index=True)
            
            # Inpatient audit
            
            audit = pd.DataFrame(columns=self.inpatient_cols)
            audit['master_unit'] = self.audit_unit_list
            audit['subunit'] = self.audit_subunit_list
            audit['inpatients'] = self._allocate.inpatient_counts.values.flatten()
            audit['day'] = self._env.now
            audit.reset_index(inplace=True)
            audit.drop('index', axis=1, inplace=True)
            
            # Add audit to existing DataFrame
            self.inpatient_audit = self.inpatient_audit.append(audit, ignore_index=True)

            # Trigger next audit after interval        
            yield self._env.timeout(self._params.audit_interval)


