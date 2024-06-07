from sim.model import DialysisSim
from sim.parameters import Scenario, Uniform


if __name__ == '__main__':
    #default params are the base case - to update...
    
    scenarios = {}
    scenarios['base'] = Scenario(total_proportion_people_infected=0.8)
    
    for name, scenario in scenarios.items():
        model = DialysisSim(scenario)
        print(f'Running {name} scenario (Single replication)')
        model.run()
        # Save audits
        model.audit.patient_audit.to_csv(f'output/{name}_patient_audit.csv', index=False)
        model.audit.unit_audit.to_csv(f'output/{name}_unit_audit.csv')
        model.audit.displaced_audit.to_csv(f'output/{name}_displaced_audit.csv')
        
        
    print('All experiments complete.')