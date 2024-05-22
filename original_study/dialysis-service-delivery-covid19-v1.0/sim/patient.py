import pandas as pd
import random


class Patient:
    """
    Patient object.
    
    Object attributes
    -----------------
    
    
    _allocate: Reference to patient-unit allocation object
    _env: Reference to model environment object
    _params: Reference to sceanrio paraemters object
    _pop: Reference to patient population object
    _units: Reference to unit object
    
    current_travel_time: current time to allocated unit
    current_unit: current unit patent allocated to
    current_unit_location: postcode of current unit
    default_time: time to unit patient allocated to in patient info CSV 
    default_unit: unit patient allocated to in patient info CSV
    default_unit_location: postcode of default unit
    displaced: Whether patient is dispalced from default unit (True/False)
    displaced_additional_time: Additional travel time if displaced
    dialysis_type: Dialysis type (HD unit or home)
    first_day: First day of the week for dialysis (Mon or Tues)
    inpatient_los: inpatient length of stay if inpatient stay required
    location: Patient home location (postcode sector)
    patient_id: id of patient (allocated in model)
    require_inpatient: Whether patient will need inpation care (True/False)
    session: Current session at unit
    status: COVID status (negative, positive, recovered, died)
    time_in: Sim time patient created
    time_positive: Amount of time spent as COVID +ve outpatient
    time_to_infection: Time from mdoel start that patient becomes infected
    unallocated_to_session: Currently unallocated to any saession (True/False)
    will_be_infected: Patient will be infected in model (True/False)
    
    Methods
    -------
    patient_virus_progress:
        Progress patient through negative --> positive --> recover or die.
        Death occurs at end of positive episode. Patient may start the model in
        any state
        
    """

    def __init__(self, env, patient_data, allocate, params, pop, units):
        
        """Constructor method for new patient. Patient data is passed as a
        dictionary"""

        self._allocate = allocate
        self.current_travel_time = 0
        self.current_unit = patient_data['default_unit']
        self.current_unit_location = patient_data['default_unit_location']
        self.default_time = 0
        self.default_unit = patient_data['default_unit']
        self.default_unit_location = patient_data['default_unit_location']
        self.displaced = False
        self.displaced_additional_time = 0
        self.dialysis_type = patient_data['dialysis_type']
        self._env = env
        self.first_day = patient_data['first_day']
        self.inpatient_los = patient_data['inpatient_los']
        self.location = patient_data['location']
        self._params = params
        self.patient_id = patient_data['patient_id']
        self._pop = pop
        self.require_inpatient = patient_data['require_inpatient']
        self.session = 'none'
        self.status = patient_data['status']
        self.time_in = env.now
        self.time_positive = patient_data['time_positive']
        self.time_to_infection = patient_data['time_to_infection']
        self.unallocated_to_session = False
        self._units = units
        self.will_be_infected = patient_data['will_be_infected']
        
        # Add travel times to non-home :
        if self.default_unit_location != 'HOME':
            self.current_travel_time = units.travel_times.loc[patient_data['location']][
                patient_data['default_unit_location']]
            self.default_time = self.current_travel_time
            self.displaced_additional_time = 0
            

        # Apply random positives
        if (self.status == 'negative' and random.random() < 
            self._params.random_positive_rate_at_start):
            self.status = 'positive'
        
        
    def patient_virus_progress(self):
        """
        Progress patient through negative --> positive --> recover or die.
        Death occurs at end of positive episode. Patient may start the model in
        any state.
        """
        
        # Period as negative COVID
        if self.status == 'negative':
            
            # Period of cov negative:
            yield self._env.timeout(self.time_to_infection)
            
            # End of negative period, remove from patient allocation
            self._allocate.remove_patient(self)
            
            # Switch status to positive and re-allocate
            self.status = 'positive'            
            
            # If previously unallocated, remove from list of unallocated patients
            if self in self._pop.unallocated_patients:
                self._pop.unallocated_patients.remove(self)  

            # Allocate patient
            self._allocate.allocate_patient(self)
            
            # Add to appropriate patient list
            self._pop.positive_patients.append(self)
            
        # Period of positive COVID
        if self.status == 'positive': 
                    
            # Period of Cov positive
            yield self._env.timeout(self.time_positive)
            
            # End of positive period, remove from patient allocation and reset location
            self._allocate.remove_patient(self)            
                        
            # If previously unallocated, remove from list of unallocated patients
            if self in self._pop.unallocated_patients:
                self._pop.unallocated_patients.remove(self)
            
            # Check for inpatient stay
            if self.require_inpatient:
          
                self.status = 'inpatient'
                self._pop.inpatients.append(self)
                
                self._allocate.allocate_inpatient(self)
                
                # Time in inpatient
                yield self._env.timeout(self.inpatient_los)
                
                self._pop.inpatients.remove(self)
                self._allocate.inpatient_counts.loc[self.current_unit] -= 1
            
            # Check for mortality at end of positive (+ inpatient) phase
            if self._params.mortality_rand.sample() < self._params.mortality:
                
                # PATIENT DIES
                self.status = 'died'
                
                # Add to appropriate patient list
                self._pop.died_patients.append(self)

                # No allocation of patient required
                self.current_unit = 'none'
                self.session = 'none'
            
            else:
                # PATIENT RECOVERS
                self.status = 'recovered'
                
                # Allocate patient
                self._allocate.allocate_patient(self)
                
                # Add to appropriate patient list
                self._pop.recovered_patients.append(self)

            