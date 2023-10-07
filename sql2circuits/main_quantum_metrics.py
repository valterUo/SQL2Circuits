

import csv
import os
import pickle
from circuit_preparation.circuits import Circuits
from data_preparation.database import Database
from data_preparation.prepare import DataPreparation
from data_preparation.queries import QueryGenerator
from evaluation.quantum_metrics import EntanglingCapability, Expressibility
this_folder = os.path.abspath(os.getcwd())

run_id = 3
classification = 3
workload_type = "cardinality"
seed = "data_preparation//query_seeds//JOB_query_seed_cardinality_big.json"
output_folder = this_folder + "//circuit_preparation//data//circuits//" + str(run_id) + "//"
database = Database("IMDB")
generator = QueryGenerator(run_id, workload_type=workload_type, database="IMDB", query_seed_file_path=seed)
query_file = generator.get_query_file()
data_preparator = DataPreparation(run_id, query_file, database=database, workload_type=workload_type, classification=classification)
total_number_of_circuits = len(data_preparator.get_training_data_labels())
circuits = Circuits(run_id, query_file, output_folder=output_folder, classification=classification, write_cfg_to_file=True, write_pregroup_to_file=True, generate_circuit_png_diagrams=True)
circuits.execute_full_transformation()
circuits.generate_pennylane_circuits()
do_expressibility = False
do_entangling_capability = True

if do_expressibility:
    expressibility = Expressibility(circuits, classification)
    expressibility.calculate_expressibility()
    expressibility.plot_expressibility()
    expressibility.calculate_kl_div()
    expressibility.calculate_js_div()

if do_entangling_capability:
    
    entangling_capability = EntanglingCapability(circuits)
    sample_size = 10
    res = entangling_capability.mw_engtanglement(sample_size)
    
    #file = this_folder + 'evaluation//results//mw_engtanglement_' + str(classification) + '.pickle'
    csv_file = this_folder + '//evaluation//results//mw_engtanglement_' + str(classification) + '.csv'
    
    #with open(file, 'wb') as handle:
    #    pickle.dump(res, handle, protocol=pickle.HIGHEST_PROTOCOL)
        
    #res = {}
    #with open(file, 'rb') as handle:
    #    res = pickle.load(handle)
    
    header = ['id', 'engtangling_capability']
    with open(csv_file, 'w', encoding='UTF8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for k in sorted([int(key) for key in res.keys()]):
            writer.writerow([str(k), res[str(k)]])

    total = 0
    for k in res:
        total += float(res[k])
    print(total/len(res))
