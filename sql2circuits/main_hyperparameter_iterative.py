import os
import json
import numpy as np
from data_preparation.queries import QueryGenerator
from data_preparation.prepare import DataPreparation
from data_preparation.database import Database
from circuit_preparation.circuits import Circuits
from training.train import SQL2CircuitsEstimator
from training.sample_feature_preparation import SampleFeaturePreparator
from skopt import BayesSearchCV
from skopt.space import Real

this_folder = os.path.abspath(os.getcwd())
seed_paths = ["data_preparation//query_seeds//JOB_query_seed_execution_time.json",
              "data_preparation//query_seeds//JOB_query_seed_cardinality.json"]
workload_types = ["execution_time", "cardinality"]
run_id = 1
ty = 1
workload_type = workload_types[ty]
database = Database("IMDB")
generator = QueryGenerator(run_id, workload_type = "cardinality", database = "IMDB", query_seed_file_path = seed_paths[ty])
query_file = generator.get_query_file()
data_preparator = DataPreparation(run_id, query_file, database = database, workload_type = workload_type, classification = 2)

this_folder = os.path.abspath(os.getcwd())
output_folder = this_folder + "//circuit_preparation//data//circuits//" + str(run_id) + "//"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    print("The new directory: ", output_folder, " is created.")

circuits = Circuits(run_id, query_file, output_folder, write_cfg_to_file = True, write_pregroup_to_file=True, generate_circuit_png_diagrams = True)
circuits.execute_full_transformation()

optimization_method = "Pennylane"
initial_number_of_circuits = 160
number_of_circuits_to_add = 20
total_number_of_circuits = len(data_preparator.get_training_data_labels())
a = 0.01358891418726149
c = 0.08991002793500955

for i in range(initial_number_of_circuits, total_number_of_circuits, number_of_circuits_to_add):
    sf = SampleFeaturePreparator(run_id, data_preparator, circuits, i, optimization_method)
    X_train = sf.get_X_train()
    X_valid = sf.get_X_valid()
    y = sf.get_y()

    opt = BayesSearchCV(
        SQL2CircuitsEstimator(run_id,
                        circuits = circuits,
                        workload = "cardinality",
                        classification = 2,
                        a = a,
                        c = c,
                        optimization_method = optimization_method,
                        epochs = 1000), 
                        { 'a': Real(0.0001, 0.1, 'uniform'), 
                            'c': Real(0.0001, 0.1, 'uniform') }, 
                            n_iter = 10)

    opt.fit(X_train, y, X_valid = X_valid)

    results = dict(opt.cv_results_)
    for key, value in results.items():
        if isinstance(value, np.ndarray):
            results[key] = value.tolist()
    best_params = dict(opt.best_params_)
    for key, value in best_params.items():
        if isinstance(value, np.ndarray):
            best_params[key] = value.tolist()
    a = best_params["a"]
    c = best_params["c"]
    results["best_params"] = best_params
    with open("training//results//" + str(run_id) + "//" + str(i) + "_" + str(run_id) + "_cv_results_.json", "w") as f:
        json.dump(results, f)