import os
from data_preparation.queries import QueryGenerator
from data_preparation.prepare import DataPreparation
from data_preparation.database import Database
from circuit_preparation.circuits import Circuits
from sql2circuits.training.pennylane_train import SQL2CircuitsEstimatorPennylane
from training.train import SQL2CircuitsEstimator
from training.sample_feature_preparation import SampleFeaturePreparator

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

trainer = SQL2CircuitsEstimatorPennylane()

sf = SampleFeaturePreparator(run_id, data_preparator, circuits, "all", "Pennylane")
X_train = sf.get_X_train()
X_valid = sf.get_X_valid()
y = sf.get_y()

trainer.fit(X_train, y, X_valid = X_valid, save_parameters = True)