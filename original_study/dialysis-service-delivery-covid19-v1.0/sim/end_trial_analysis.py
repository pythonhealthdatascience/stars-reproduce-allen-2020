import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math


class EndTrialAnalysis:
    """
    Analysis run at end of replicate runs.
    
    Generates and saves three charts:
        
        * Displaced: charts number of patients displaced from their home units,
          and average additional travel time (one way)
        * Patients: charts number of patients by COVID status + number of patients unallocated
          to any unit session
        * Units: charts number of COV -ve, +ve and inpatients in each unit
     
        
    Object attributes
    -----------------
    
    Pivot tables aggregate data from multiple runs
    
    name: scenario name
    unit_names: list of unit names (subunits will be combined together) 
    d_audit_pivot: displaced patient audit pivoted by day
    p_audit_pivot: patient audit pivoted by day
    u_audit: unit audit pivoted by day
    i_audit_pivot: inpatient audit pivoted by day
    

    # Methods
    ---------    
    
    plot_displaced_audit:
        Charts number of patients displaced from their home units, and average additional
        travel time (one way). Saves figure.
        
    plot_patient_audit:
        Charts number of patients by COVID status + number of patients unallocated
        to any unit session. Saves figure
        
    plot_unit_audit:
        Charts number of COV -ve, +ve and inpatients in each unit. Saves figure.
        
    
    
    
    """
    
    
    def __init__(self, name, p_audit, u_audit, d_audit, i_audit):
        
        """
        Constructor method prepares data for plotting.
        
        Pivot tables aggregate data from multiple runs
        
        d_audit_pivot: displaced patient audit pivoted by day
        p_audit_pivot: patient audit pivoted by day
        u_audit: unit audit pivoted by day
        i_audit_pivot: inpatient audit pivoted by day
        """
               
        self.name = name
        
        self.unit_names = list(set(u_audit['master_unit']))
        
        # Displaced patient audit (convert numeric data to float to avoid castign error in pivot)
        
        data_cols = ['number','add_time_min', 'add_time_1Q', 'add_time_median', 'add_time_3Q',
                        'add_time_max', 'add_time_total']
        
        d_audit[data_cols] = d_audit[data_cols].astype('float')
        
        self.d_audit_pivot = d_audit.pivot_table(index=['day'],
                values=data_cols,
                aggfunc=[np.median, np.min, np.max],
                margins=False) # margins summarises all
        
        # Patient audit (convert numeric data to float to avoid castign error in pivot)
        
        data_cols = ['negative','positive', 'recovered', 'inpatient', 'died', 'unallocated']
        
        p_audit[data_cols] = p_audit[data_cols].astype('float')
        
        self.p_audit_pivot = p_audit.pivot_table(index=['day'],
                values=data_cols,
                aggfunc=[np.median, np.min, np.max],
                margins=False) # margins summarises all
        
        # Unit audit (convert numeric data to float to avoid castign error in pivot)
        
        data_cols = ['negative','positive', 'recovered','neg+rec', 'total']
        
        u_audit[data_cols] = u_audit[data_cols].astype('float')
        
        
        u_audit_sum_master_units = u_audit.pivot_table(index=['scenario', 'day', 'master_unit'],
                values=data_cols,
                aggfunc=[np.sum],
                margins=False)
        
        self.u_audit_pivot = u_audit_sum_master_units['sum'].pivot_table(
                index=['day', 'master_unit'],
                values=data_cols,
                aggfunc=[np.median, np.min, np.max],
                margins=False) # margins summarises all
        
        # Inpatient audit
        
        # Dummy column added as pivot was misbehaving with only one data column!
        
        i_audit['dummy'] = 1
        
        data_cols = ['inpatients', 'dummy']
        i_audit[data_cols] = i_audit[data_cols].astype('float')
        
        inpatient_audit_sum_master_units = i_audit.pivot_table(
                index=['scenario', 'day', 'master_unit'],
                values=data_cols,
                aggfunc=[np.sum],
                margins=False)
        
   
        self.i_audit_pivot = inpatient_audit_sum_master_units['sum'].pivot_table(
                index=['day', 'master_unit'],
                values=data_cols,
                aggfunc=[np.median, np.min, np.max],
                margins=False) # margins summarises all
                

    def plot_displaced_audit(self):
        """
        Charts number of patients displaced from their home units, and average additional travel
        time (one way). Saves figure.
        """
        
        # Set up chart
        fig = plt.figure(figsize=(9,6))
        
        # ax1 = plot of numbers of displaced patients
        ax1 = fig.add_subplot(121)
        ax1.plot(self.d_audit_pivot['median']['number'], color='b')
        ax1.plot(self.d_audit_pivot['amin']['number'], lw=0.25, color='b')
        ax1.plot(self.d_audit_pivot['amax']['number'], lw=0.25, color='b')
        ax1.grid()
        ax1.set_xlabel('Day')
        ax1.set_ylabel('Number of patients')
        ax1.set_title('Number of displaced patients')
        
        # ax2 = plot of additonal travel times        
        ax2 = fig.add_subplot(122)
        ax2.plot(self.d_audit_pivot['median']['add_time_1Q'], color='y', label = 'Quartile 1')
        ax2.plot(self.d_audit_pivot['median']['add_time_median'], color='g', label = 'Median')
        ax2.plot(self.d_audit_pivot['median']['add_time_3Q'], color='b', label = 'Quartile 3')
        ax2.plot(self.d_audit_pivot['median']['add_time_max'], color='r', label = 'Maximum')        
        ax2.set_xlabel('Day')
        ax2.set_ylabel('Additional travel time (mins)')
        ax2.legend()
        # Add min and max (after legend, so not in legend)        
        ax2.plot(self.d_audit_pivot['amin']['add_time_1Q'], color='y', lw=0.25)
        ax2.plot(self.d_audit_pivot['amax']['add_time_1Q'], color='y', lw=0.25)
        ax2.plot(self.d_audit_pivot['amin']['add_time_median'], color='g', lw=0.25)
        ax2.plot(self.d_audit_pivot['amax']['add_time_median'], color='g', lw=0.25)
        ax2.plot(self.d_audit_pivot['amin']['add_time_3Q'],  color='b', lw=0.25)
        ax2.plot(self.d_audit_pivot['amax']['add_time_3Q'],  color='b', lw=0.25)
        ax2.plot(self.d_audit_pivot['amin']['add_time_max'], color='r', lw=0.25)
        ax2.plot(self.d_audit_pivot['amax']['add_time_max'], color='r', lw=0.25)
        ax2.set_title('Additional travel time for displaced patients')
        ax2.grid()
        
        # Finalise chart and save
        plt.tight_layout(pad=3)
        plt.savefig(f'output/displaced_{self.name}.png')
        plt.show()
        

    def plot_patient_audit(self):
        """
        Charts number of patients by COVID status + number of patients unallocated
          to any unit session. Saves figure.
        """
        
        # Set up chart
        fig = plt.figure(figsize=(6,6))
        ax1 = fig.add_subplot(111)
        
        # Plot median patients counts on same chart
        ax1.plot(self.p_audit_pivot['median']['negative'], color='b', label='Negative')
        ax1.plot(self.p_audit_pivot['median']['positive'], color='r', label='Positive outpatient')
        ax1.plot(self.p_audit_pivot['median']['recovered'], color='g', label='Recovered')
        ax1.plot(self.p_audit_pivot['median']['inpatient'], color='y', label='Positive inpatient')
        ax1.plot(self.p_audit_pivot['median']['died'], color='k', label='Died')
        ax1.plot(self.p_audit_pivot['median']['unallocated'], color='m', label='Unallocated')
        ax1.set_xlabel('Days')
        ax1.set_ylabel('Patients')
        ax1.legend()        
        # Add min and max lines (after legend created)     
        ax1.plot(self.p_audit_pivot['amin']['negative'], lw=0.25, color='b')        
        ax1.plot(self.p_audit_pivot['amax']['negative'], lw=0.25, color='b')
        ax1.plot(self.p_audit_pivot['amin']['recovered'], lw=0.25, color='g')
        ax1.plot(self.p_audit_pivot['amax']['recovered'], lw=0.25, color='g')       
        ax1.plot(self.p_audit_pivot['amax']['positive'], lw=0.25, color='r')
        ax1.plot(self.p_audit_pivot['amin']['positive'], lw=0.25, color='r')
        ax1.plot(self.p_audit_pivot['amax']['unallocated'], lw=0.25, color='m')
        ax1.plot(self.p_audit_pivot['amin']['unallocated'], lw=0.25, color='m')
        ax1.plot(self.p_audit_pivot['amax']['inpatient'], lw=0.25, color='y')
        ax1.plot(self.p_audit_pivot['amin']['inpatient'], lw=0.25, color='y')
        ax1.plot(self.p_audit_pivot['amax']['died'], lw=0.25, color='k')        
        ax1.plot(self.p_audit_pivot['amin']['died'], lw=0.25, color='k')
        ax1.grid()
        
        # Finalise chart and save
        plt.tight_layout(pad=3)
        plt.savefig(f'output/patients_{self.name}.png')
        plt.show()
        
        
    def plot_unit_audit(self):
        """
        Charts number of COV -ve, +ve and inpatients in each unit. Saves figure.
        """

        # Copy unit and inpatient audits
        df_u = self.u_audit_pivot.copy()
        df_i = self.i_audit_pivot.copy()
        
        # Drop 'home' unit from audit and get amended unit list and length
        mask = df_u.index.get_level_values('master_unit') != 'HOME'
        units = self.unit_names.copy()
        units.remove('HOME')
        units.sort()
        df_u = df_u[mask]
        df_i = df_i[mask]
        unit_count = len(units)
        
        # Calculate number of rows and columns for charts to use
        cols = math.floor(math.sqrt(unit_count))
        rows = math.ceil(unit_count / cols)
        
        # Set up chart
        fig = plt.figure(figsize=(12,12))
        
        # Loop through units
        for num, unit in enumerate(units):
            # Get unit and inpatient data for unit in loop
            unit_data = df_u.iloc[df_u.index.get_level_values('master_unit') == unit]
            inpatients = df_i.iloc[df_i.index.get_level_values('master_unit') == unit]
            
            # Add a chart
            ax = fig.add_subplot(rows, cols, num + 1)
            # Plot median values
            ax.plot(unit_data['median']['neg+rec'].values, color = 'g', label='Neg + Rec')
            ax.plot(unit_data['median']['positive'].values, color = 'r', label='Positive outpatient')
            ax.plot(inpatients['median']['inpatients'].values, color = 'b', label='Postive inpatient')
            ax.legend()
            # Add min and max lines after legend
            ax.plot(unit_data['amin']['neg+rec'].values, color = 'g', lw=0.25)
            ax.plot(unit_data['amax']['neg+rec'].values, color = 'g', lw=0.25)
            ax.plot(unit_data['amin']['positive'].values, color = 'r', lw=0.25)
            ax.plot(unit_data['amax']['positive'].values, color = 'r', lw=0.25)
            ax.plot(inpatients['amin']['inpatients'].values, color = 'b', lw=0.25)
            ax.plot(inpatients['amax']['inpatients'].values, color = 'b', lw=0.25)
            # Add axis label, title and grid
            ax.set_ylim(0)
            ax.set_xlabel('Day')
            ax.set_ylabel('Patient count')
            ax.set_title(unit)
            ax.grid()   
        
        # Finalise chart and save
        plt.tight_layout(pad=3)
        plt.savefig(f'output/units_{self.name}.png')
        plt.show()
            

            
            
                
                
                
        
        
                         
        

