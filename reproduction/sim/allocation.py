import pandas as pd

class AllocatePatients:
    """A collection of methods to allocate patients to units and shifts
    
    Object attributes
    -----------------
    
    _params: Reference to sceanrio paramters object
    _pop: Reference to model patient population object   
    count_day_swaps: Number of times patients have had to change sessions    
    count_total_patients: total patients loaded  
    count_status: Number of sessions allocated to COVID negative/positive patients
    inpatient_counts: Count of inpatients at each subunit
    inpatient_units: List of whether subunits accept inpatients 
    travel_times: DataFrame of travel times from patient postcode sector to each unit
    unit_chairs: Number of chairs in each unit (or subunit)
    unit_list: List of all units (or subunit (where unit is split))
    unit_location_lookup: dictionary, key=subunit name, value=subunit postcode
    unit_order_by_patient_postcode: List of units ordered by proximity to patient postcode
    unit_order_given: List of preferred order of subunits for COVID-positive patients
    unit_sessions: A DataFrame of status of each subunit/session (negative/positive/closed)
    unit_sessions_count: DataFrame on number of aptients allocated to each subunit/session
    
    
    Methods
    -------
    
    allocate_cov_neg_patient:
        Allocate a COVID -ve patient to subunit session
        
    allocate_cov_pos_patient:
        Allocate a COVID -+e patient to subunit session
        
    allocate_inpatient:
        Allocate a COVID +ve patient to inpatient care when necessary
        
    allocate_patient: 
        Allocates patients to sessions. Calls appropriate method for patient
        COVID status. Adds travel time for patients.
    
    check_availability_in_session:
        Checks availability in a list of sessions
        
    load_patient:
        Inital load of patients into system
        
    remove_patient:
        Remove patient from appropriate counts and lists
    

    """
    def __init__(self, _units, _params, _pop):
        """
        Constructor method.

        Parameters
        ----------
        _params : Object
            Sceanrio paramaters object.
        _pop : Object
            Object holding patient populations (all patients, patients by COVID
            stage, inpatients).
        _units : Object
            Object holding information on units

        Returns
        -------
        None.

        """
        
        self._params = _params
        self._pop = _pop
        
        units_input = _units.unit_info
        
        self.unit_list = list(units_input['subunit']) + ['HOME']
        unit_chairs = list(units_input['Chairs']) + [9999]
        
        self.unit_location_lookup = _units.location_lookup
        self.travel_times = _units.travel_times

        self.inpatient_units = units_input[['subunit', 'inpatient']]
        self.inpatient_units.set_index('subunit', inplace=True)
        
        
        # Set up units. Start by allocating all shifts -ve (and shift 4 closed)
        self.unit_sessions = pd.DataFrame(index=self.unit_list)
        
        # set up available shifts (avalable shifts all set to 'neg).Miss out home location.
        # Create columns for shifts and set all to negative
        self.unit_sessions = self.unit_sessions.assign(Mon_1 = 'negative', Mon_2 = 'negative', 
                Mon_3 = 'negative', Tues_1 = 'negative', Tues_2 = 'negative', Tues_3 = 'negative')
        
        # Close unit shifts where not available (read from input sheet, avoid 'last entry of HOME')
        if self._params.open_all_sessions == False:
            for subunit in self.unit_list[0:-1]:
                unit_info = units_input[units_input['subunit'] == subunit]
                for session in ['Mon_1', 'Mon_2', 'Mon_3', 'Tues_1', 'Tues_2', 'Tues_3']:
                    if unit_info[session].values != 1:
                        # Session closed (not available)
                        self.unit_sessions.loc[subunit][session] = 'x'
        
        # Set numebr of chairs in each subunit                
        self.unit_chairs = pd.DataFrame(index=self.unit_list)
        self.unit_chairs['chairs'] = unit_chairs
        
        # Set up patient counter table
        self.unit_sessions_count = self.unit_sessions.copy()
        self.unit_sessions_count[['Mon_1', 'Mon_2', 'Mon_3', 'Tues_1', 'Tues_2', 'Tues_3']] = 0
        
        # Overall counts
        self.count_total_patients = 0
        self.count_status = {'negative': 0, 'positive': 0, 'recovered': 0, 'died': 0}
        self.count_day_swaps = 0
        
        # Inpatient counts
        self.inpatient_counts = pd.DataFrame(index=self.unit_list)
        self.inpatient_counts['inpatients'] = 0
        
        
        # Unit preferences
        self.unit_order_by_patient_postcode = _units.unit_preferences
        self.unit_order_given = _units.given_order
                
        
    def allocate_cov_neg_patient(self, patient):
        """
        Allocate a COVID -ve patient to subunit session. Preference:
            1) Try assigning to local unit with current allocated day
            2) Try assigning to local unit on any day
            3) Check all units (ordered by proximity)
        
        Parameters
        ----------
        patient : Object
            Paotient object (information on individual patient).

        Returns
        -------
        None.

        """
        
        first_day = patient.first_day        
        sessions_to_check = [first_day+'_1', first_day+'_2', first_day+'_3']
        
        # 1) Try assigning to local unit first
        
        units_to_check = patient.default_unit
        for unit_to_check in units_to_check:            
            self.check_availability_in_session(patient, unit_to_check, sessions_to_check, 
                                               'negative')
            if patient.unallocated_to_session == False:
                break
                        
            
        #2) If no availabilty check all day sessions
        
        if patient.unallocated_to_session:
            sessions_to_check = ['Mon_1', 'Mon_2', 'Mon_3', 'Tues_1', 'Tues_2', 'Tues_3']
            units_to_check = patient.default_unit
            for unit_to_check in units_to_check:            
                self.check_availability_in_session(patient, unit_to_check, sessions_to_check, 
                                                   'negative')
                if patient.unallocated_to_session == False:
                    break
            
        #3) If no availability check other units

        if patient.unallocated_to_session:
            sessions_to_check = ['Mon_1', 'Mon_2', 'Mon_3', 'Tues_1', 'Tues_2', 'Tues_3']
            units_to_check = self.unit_order_by_patient_postcode.loc[patient.location] 

            for unit_to_check in units_to_check:
                self.check_availability_in_session(
                    patient, unit_to_check, sessions_to_check, 'negative')
                # Change day if successful
                if patient.unallocated_to_session == False:
                    break

        
    
    def allocate_cov_pos_patient(self, patient):
        """
        Allocate a COVID +ve patient to subunit session. Preference:
            1) Try assigning to local unit with current allocated day
            2) Try assigning to local unit on any day
            3) Check all units (ordered by prescribed selection order)
            4) Designate a new session as for COVID +ve patients        

        Parameters
        ----------
        patient : Object
            Paotient object (information on individual patient).

        Returns
        -------
        None.
        """
        
        first_day = patient.first_day        
        sessions_to_check = [first_day+'_1', first_day+'_2', first_day+'_3']
        
        # 1) Try assigning to local unit first
        units_to_check = patient.default_unit
        for unit_to_check in units_to_check:            
            self.check_availability_in_session(patient, unit_to_check, sessions_to_check, 
                                               'positive')
            if patient.unallocated_to_session == False:
                    break
        
        #2) If no availabilty check all day sessions
        
        if patient.unallocated_to_session:
            sessions_to_check = ['Mon_1', 'Mon_2', 'Mon_3', 'Tues_1', 'Tues_2', 'Tues_3']
            units_to_check = patient.default_unit
            for unit_to_check in units_to_check:            
                self.check_availability_in_session(patient, unit_to_check, sessions_to_check, 
                                                   'positive')
                if patient.unallocated_to_session == False:
                    break
            
        #3) If no availability check other units
            
        if patient.unallocated_to_session:
            sessions_to_check = ['Mon_1', 'Mon_2', 'Mon_3', 'Tues_1', 'Tues_2', 'Tues_3']
            units_to_check = self.unit_order_given

            for unit_to_check in units_to_check:
                self.check_availability_in_session(
                    patient, unit_to_check, sessions_to_check, 'positive')
                # Change day if successful
                if patient.unallocated_to_session == False:
                    break
                
        ################ Need to open a new cov +ve session ###################
        ## Work through prescribed list of units - clear a session as needed ##
                
        if patient.unallocated_to_session:
            units_to_check = self.unit_order_given
            sessions_to_check = ['Mon_1', 'Mon_2', 'Mon_3', 'Tues_1', 'Tues_2', 'Tues_3']
            for unit in units_to_check:
                if patient.unallocated_to_session:
                    for session in sessions_to_check:   
                       if self.unit_sessions.loc[unit][session] == 'negative':
                           # Move patients to be reallocated and reassign to cov +ve
                           self.unit_sessions.loc[unit][session] = 'positive'
                           self.unit_sessions_count.loc[unit][session] = 0
                           # Remove all current patients in that session
                           for session_patient in self._pop.negative_patients:
                               if (session_patient.current_unit == unit and 
                                   session_patient.session == session):
                                       session_patient.current_unit = 'none'
                                       session_patient.session = 'none'
                                       session_patient.unallocated_to_session = True
                           # Assign patient
                           patient.current_unit = unit
                           self.check_availability_in_session(patient, unit, [session], 'positive')
                           break
        

    def allocate_inpatient(self, patient):
        """
        Allocate a COVID +ve patient to inpatient care when necessary. Searches through units by
        by proximity to patient postcode and checks whether unit accepts inpatients.

        Parameters
        ----------
        patient : Object
            Paotient object (information on individual patient).

        Returns
        -------
        None.

        """

        units_to_check = self.unit_order_by_patient_postcode.loc[patient.location] 

        for unit_to_check in units_to_check:
            if self.inpatient_units.loc[unit_to_check].values[0] == 1:
                patient.current_unit = unit_to_check
                self.inpatient_counts.loc[unit_to_check]['inpatients'] += 1
                break
            
    
    def allocate_patient(self, patient):
        """
        Allocates patients to sessions. Calls appropriate method for patient
        COVID status. Adds travel time for patients.

        Parameters
        ----------
        patient : Object
            Paotient object (information on individual patient).

        Returns
        -------
        None.

        """
        
        # Reset patient allocation status
        patient.session = 'none'
        patient.unallocated_to_session = True
       
        # Define dictionary to call function based on patient's cov status
        func_dict = {'negative': self.allocate_cov_neg_patient,
                     'positive': self.allocate_cov_pos_patient,
                     'recovered': self.allocate_cov_neg_patient}
        
        function_to_call = func_dict[patient.status]
        function_to_call(patient)
        
        # Unallocated patients
        if patient.unallocated_to_session:
            self._pop.unallocated_patients.append(patient)
        
        # Add allocated unit location
        if patient.current_unit != 'HOME':
            patient.current_unit_location = self.unit_location_lookup[patient.current_unit]
        
        # Add travel times to non-home for allocated patients:
        if patient.unallocated_to_session == False and (
                patient.current_unit_location != patient.default_unit_location):
                patient.displaced = True
                patient.current_travel_time = \
                    self.travel_times.loc[patient.location][patient.current_unit_location]
                patient.displaced_additional_time = \
                    patient.current_travel_time - patient.default_time
                self._pop.displaced_patients.append(patient)

    
    def check_availability_in_session(self, patient, unit, sessions_to_check, session_type):
            """
            Loop through sessions of a particular type (cov negative/psotive) and check for free
            chair.

            Parameters
            ----------
            patient : patient object
                A single patient.
            sessions_to_check : list
               The list of session to check for each unit
            session_type : string
                Type of session: 'negative' or 'positive'.

            Returns
            -------
            session_allocated : bool
                True of free session chair has been found, otherwsie False.

            """
            
            patient.unallocated_to_session = True
            for session in sessions_to_check:
                if self.unit_sessions.loc[unit][session] == session_type:
                    has_capacity = (self.unit_sessions_count.loc[unit][session] < 
                        self.unit_chairs.loc[unit]['chairs'])
                    if has_capacity:
                        # Chair free to be allocated
                        self.unit_sessions_count.loc[unit][session] += 1
                        patient.session = session
                        patient.current_unit = unit
                        patient.unallocated_to_session = False
                        break



    def load_patient(self, patient):
        """
        Inital load of patients into system. Adds to population patient dictionary,
        and appropriate population patient list by COVID status.

        Parameters
        ----------
        patient : Object
            Paotient object (information on individual patient).

        Returns
        -------
        None.

        """
            
        # Maintain patient count 
        self.count_total_patients += 1
        
        # Allocate patient to subunit/session
        self.allocate_patient(patient)
        
        # Add to appropriate _population lists
        patient_dict = {'negative': self._pop.negative_patients, 
                         'positive': self._pop.positive_patients,
                         'recovered': self._pop.recovered_patients,
                         'died': self._pop.died_patients}
        
        # Add to population dictionary of all patients
        patient_dict[patient.status].append(patient)       
                
    
    def remove_patient(self, patient):
        """
        Remove patient from appropriate counts and lists.

        Parameters
        ----------
        patient : patient object
            A single patient.

        Returns
        -------
        None.

        """
        
        # Remove patient from subunit/session (unless not allocated to subunit/session)
        if not patient.unallocated_to_session:
            self.unit_sessions_count.loc[patient.current_unit][patient.session] -= 1
        
        # Remove from appropriate _population lists (use dict to select appropriate list)
        patient_dict = {'negative': self._pop.negative_patients, 
                         'positive': self._pop.positive_patients,
                         'recovered': self._pop.recovered_patients}
        patient_dict[patient.status].remove(patient)
                
        # Reset patient displacement from default unit
        patient.displaced = False
        patient.displaced_additional_time = True
        if patient in self._pop.displaced_patients:
            self._pop.displaced_patients.remove(patient)

        # If positive patient check if session can be re-allocated to cov negative
        if patient.status == 'positive' and patient.session != 'none':
            if self.unit_sessions_count.loc[patient.current_unit][patient.session] == 0:
                self.unit_sessions.loc[patient.current_unit][patient.session] = 'negative'
            

            
            
        
