import json
import pickle
import os
from training.cost_accuracy import CostAccuracy
from training.functions.pennylane_functions import make_pennylane_cost_fn, make_pennylane_pred_fn
from training.utils import multi_class_acc, multi_class_loss
this_folder = os.path.abspath(os.getcwd())


class EvaluationIQM:
    
    def __init__(self, run_id, identifier, result_params_file, test_circuits, test_labels, test_params = None) -> None:
        self.run_id = run_id
        self.identifier = identifier
        self.result_params = None
        # Open pickled result params file
        with open(result_params_file, "rb") as f:
            self.result_params = pickle.load(f)
        self.test_circuits = test_circuits
        self.test_labels = test_labels
        self.params = test_params
        self.test_result_file = "training//results//" + str(self.run_id) + "//" + str(self.run_id) + "_test_results.json"
        self.loss_function = multi_class_loss
        self.accuracy = multi_class_acc
        
    def evaluate_on_IQM(self):
        test_pred_fn = make_pennylane_IQM_pred_fn(self.test_circuits)
        costs_accuracies = CostAccuracy()
        test_cost_fn = make_pennylane_cost_fn(test_pred_fn, self.test_labels, self.loss_function, self.accuracy, costs_accuracies, "test")
        test_cost_fn(self.result_params.x) # type: ignore
        test_accs = costs_accuracies.get_test_accs()