import os
import json
from data_preparation.queries import QueryGenerator
from data_preparation.prepare import DataPreparation
from data_preparation.database import Database
from circuit_preparation.circuits import Circuits
from evaluation.evaluation import Evaluation
from docs.drafts.train import SQL2CircuitsEstimator
from sql2circuits.training.data_preparation_manager import DataPreparationManager
this_folder = os.path.abspath(os.getcwd())
configurations = json.load(open("sql2circuits_config.json", "r"))
iterative = True

# We select a combination experiments, frameworks 
# and classical optimizers to train and evaluate the model
seed_file = configurations["seed_paths"][1]
qc_framework = configurations["qc_frameworks"][1]
classical_optimizer = configurations["classical_optimizers"][0]
measurement = configurations["measurements"][0]
workload_type = configurations["workload_types"][1]

run_id = 1
identifier = str(run_id) + "_" + qc_framework + "_" + classical_optimizer + "_" + measurement + "_" + workload_type
database = Database("IMDB")
generator = QueryGenerator(run_id, workload_type = workload_type, database = "IMDB", query_seed_file_path = seed_file)
query_file = generator.get_query_file()
data_preparator = DataPreparation(run_id, query_file, database = database, workload_type = workload_type, classification = 2)

output_folder = this_folder + "//circuit_preparation//data//circuits//" + str(run_id) + "//"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    print("The new directory: ", output_folder, " is created.")

circuits = Circuits(run_id, query_file, output_folder, write_cfg_to_file = True, write_pregroup_to_file=True, generate_circuit_png_diagrams = True)
circuits.execute_full_transformation()

#optimization_method = "Pennylane"
initial_number_of_circuits = 20
number_of_circuits_to_add = 20
total_number_of_circuits = len(data_preparator.get_training_data_labels())
a, c = 1, 1

for i in range(initial_number_of_circuits, total_number_of_circuits, number_of_circuits_to_add):

    with open("training//results//" + str(run_id) + "//" + str(i) + "_" + str(run_id) + "_cv_results_.json", "r") as f:
        param_file = json.load(f)
        a = param_file["best_params"]["a"]
        c = param_file["best_params"]["c"]

    sf = DataPreparationManager(run_id, data_preparator, circuits, i, qc_framework)
    X_train = sf.get_X_train()
    X_valid = sf.get_X_valid()
    y = sf.get_y()

    trainer = SQL2CircuitsEstimator(run_id,
                        circuits = circuits,
                        workload_type = workload_type,
                        classification = 2,
                        a = a,
                        c = c,
                        epochs = 1000,
                        qc_framework = qc_framework,
                        classical_optimizer = classical_optimizer,
                        measurement = measurement)

    result = trainer.fit_with_pennylane_noisyopt(X_train, y, X_valid = X_valid, save_parameters = True)

    evaluation = Evaluation(run_id, result, circuits, data_preparator, trainer, workload_type, i)