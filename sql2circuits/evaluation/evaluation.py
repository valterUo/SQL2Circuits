# -*- coding: utf-8 -*-

import json
import os
from training.cost_accuracy import CostAccuracy
from training.functions.lambeq_functions import make_lambeq_cost_fn, make_lambeq_pred_fn
from training.functions.pennylane_functions import make_pennylane_cost_fn, make_pennylane_pred_fn_for_gradient_descent
from training.utils import multi_class_acc, multi_class_loss, store_and_log
this_folder = os.path.abspath(os.getcwd())


class Evaluation:

    def __init__(self, run_id, identifier, result_params, circuits, data_preparation_manager) -> None:
        self.run_id = run_id
        self.identifier = identifier
        self.result_params = result_params
        self.data_preparation_manager = data_preparation_manager
        self.test_circuits = circuits.get_test_circuits()
        self.test_result_file = "training//results//" + str(self.run_id) + "//" + str(self.run_id) + "_test_results.json"
        self.loss_function = multi_class_loss
        self.accuracy = multi_class_acc

    
    def evaluate_lambeq_on_test_set(self, iteration, test_pred_fn, test_data_labels_l):
        test_pred_fn = make_lambeq_pred_fn(self.test_circuits)
        costs_accuracies = CostAccuracy()
        test_cost_fn = make_lambeq_cost_fn(test_pred_fn, test_data_labels_l, self.loss_function, self.accuracy, costs_accuracies, "test")
        test_cost_fn(self.result_params.x) # type: ignore
        test_accs = costs_accuracies.get_test_accs()
        test_result_file = this_folder + "//training//results//" + self.identifier + "//test_accuracy.json"
        if not os.path.isfile(test_result_file):
            with open(test_result_file, "w") as f:
                json.dump({ "results": [] }, f, indent=4)
        with open(test_result_file, "r") as f:
            file = json.load(f)
            file["results"].append({ "step": iteration, "test_accuracy": test_accs, "number_of_test_circuits": len(self.test_circuits) })
            json.dump(file, open(test_result_file, "w"), indent=4)


    def evaluate_pennylane_on_test_set(self, test_pred_fn, test_data_labels_l):
        costs_accuracies = CostAccuracy()
        test_cost_fn = make_pennylane_cost_fn(test_pred_fn, test_data_labels_l, self.loss_function, self.accuracy, costs_accuracies, "test")
        test_cost_fn(self.result_params.x) # type: ignore
        test_accs = costs_accuracies.get_test_accs()
        store_and_log(self.executions, { "test_accuracy": test_accs[0] }, self.result_file)


    def evaluate_pennylane_optax_on_test_sett(self, iteration, test_data_labels):
        test_circs = self.test_circuits.values()
        test_pred_fn = make_pennylane_pred_fn_for_gradient_descent(test_circs)
        test_acc = self.accuracy(test_pred_fn(self.result_params), test_data_labels)
        test_result_file = this_folder + "//training//results//" + self.identifier + "//test_accuracy.json"
        if not os.path.isfile(test_result_file):
            with open(test_result_file, "w") as f:
                json.dump({ "results": [] }, f, indent=4)
        with open(test_result_file, "r") as f:
            file = json.load(f)
            file["results"].append({ "step": iteration, "test_accuracy": test_acc, "number_of_test_circuits": len(test_circs) })
            json.dump(file, open(test_result_file, "w"), indent=4)