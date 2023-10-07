import json
import os
from main_trainer import SQL2Circuits

try:
    from jax.config import config
    config.update("jax_enable_x64", True)
    #config.update('jax_platform_name', 'cpu')
except ModuleNotFoundError:
    pass

this_folder = os.path.abspath(os.getcwd())
configurations = json.load(open("sql2circuits_config.json", "r"))
learning_rate = None
seed_file = configurations["seed_paths"][2]
qc_framework = configurations["qc_frameworks"][1]
classical_optimizer = configurations["classical_optimizers"][1]
measurement = configurations["measurements"][0]
workload_type = configurations["workload_types"][2]
learning_rate = None
if classical_optimizer == "optax":
    learning_rate = 0.005

model = SQL2Circuits(run_id = 5,
                     classification = 1,
                     seed_file = seed_file, 
                     qc_framework = qc_framework, 
                     classical_optimizer = classical_optimizer, 
                     measurement = measurement, 
                     workload_type = workload_type, 
                     initial_number_of_circuits = 25, 
                     number_of_circuits_to_add = 25,
                     iterative = True,
                     epochs = 100,
                     learning_rate=learning_rate)

model.train()