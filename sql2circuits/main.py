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

seed_file = configurations["seed_paths"][1]
qc_framework = configurations["qc_frameworks"][1]
classical_optimizer = configurations["classical_optimizers"][1]
measurement = configurations["measurements"][0]
workload_type = configurations["workload_types"][1]
learning_rate = None
if classical_optimizer == "optax":
    learning_rate = 0.05

model = SQL2Circuits(run_id = 3,
                     classification = 3,
                     seed_file = seed_file, 
                     qc_framework = qc_framework, 
                     classical_optimizer = classical_optimizer, 
                     measurement = measurement, 
                     workload_type = workload_type, 
                     initial_number_of_circuits = 50, 
                     number_of_circuits_to_add = 50, 
                     iterative = True,
                     epochs = 150,
                     learning_rate=learning_rate)

model.train()