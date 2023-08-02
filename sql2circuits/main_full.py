import os
from data_preparation.queries import QueryGenerator
from data_preparation.prepare import DataPreparation
from data_preparation.database import Database
from circuit_preparation.circuits import Circuits
from training.train import SQL2CircuitsEstimator
from training.sample_feature_preparation import SampleFeaturePreparator

this_folder = os.path.abspath(os.getcwd())
seed_paths = ["data_preparation//query_seeds//JOB_query_seed_execution_time.json",
              "data_preparation//query_seeds//JOB_query_seed_cardinality.json"]
workload_types = ["execution_time", "cardinality"]
run_id = 2
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

#initial_number_of_circuits = 20
#number_of_circuits_to_add = 20
#total_number_of_circuits = len(data_preparator.get_training_data_labels())

trainer = SQL2CircuitsEstimator(run_id,
                              circuits = circuits,
                              workload = "cardinality", 
                              a = 0.00535654523302626, 
                              c = 0.006793187137881445, 
                              classification = 2, 
                              optimization_method = "Pennylane")

#for i in range(initial_number_of_circuits, total_number_of_circuits, number_of_circuits_to_add):
#    sf = SampleFeaturePreparator(run_id, data_preparator, circuits, i, "pennylane")
#    X_train = sf.get_X_train()
#    X_valid = sf.get_X_valid()
#    y = sf.get_y()

    #trainer.fit_with_lambeq_noisyopt(X_train, y, X_valid = X_valid, save_parameters = True)
#    trainer.fit_with_pennylane_noisyopt(X_train, y, X_valid, save_parameters = True)
    #trainer.evaluate

# Train for the last time with all the data
sf = SampleFeaturePreparator(run_id, data_preparator, circuits, "all", "pennylane")
X_train = sf.get_X_train()
X_valid = sf.get_X_valid()
y = sf.get_y()

trainer.fit_with_pennylane_noisyopt(X_train, y, X_valid = X_valid, save_parameters = True)