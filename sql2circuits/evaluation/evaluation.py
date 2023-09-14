# -*- coding: utf-8 -*-

from sql2circuits.training.cost_accuracy import CostAccuracy
from sql2circuits.training.functions.lambeq_functions import make_lambeq_cost_fn
from sql2circuits.training.functions.pennylane_functions import make_pennylane_cost_fn
from sql2circuits.training.utils import multi_class_acc, multi_class_loss, store_and_log


class Evaluation:

    def __init__(self, run_id, result, circuits) -> None:
        self.run_id = run_id
        self.result = result
        self.test_circuits = circuits.get_test_circuits()
        self.test_result_file = "training//results//" + str(self.run_id) + "//" + str(self.run_id) + "_test_results.json"
        self.loss_function = multi_class_loss
        self.accuracy = multi_class_acc

    
    def evaluate_lambeq_on_test_set(self, test_pred_fn, test_data_labels_l):
        costs_accuracies = CostAccuracy()
        test_cost_fn = make_lambeq_cost_fn(test_pred_fn, test_data_labels_l, self.loss_function, self.accuracy, costs_accuracies, "test")
        test_cost_fn(self.result.x) # type: ignore
        test_accs = costs_accuracies.get_test_accs()
        store_and_log(0, { "test_accuracy": test_accs[0] }, self.test_result_file)

    def evaluate_pennylane_on_test_set(self, test_pred_fn, test_data_labels_l):
        costs_accuracies = CostAccuracy()
        test_cost_fn = make_pennylane_cost_fn(test_pred_fn, test_data_labels_l, self.loss_function, self.accuracy, costs_accuracies, "test")
        test_cost_fn(self.result.x) # type: ignore
        test_accs = costs_accuracies.get_test_accs()
        store_and_log(self.executions, { "test_accuracy": test_accs[0] }, self.result_file)