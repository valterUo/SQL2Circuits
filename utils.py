from pathlib import Path
import pickle
import math
import numpy as np
#from jax import numpy as np
i = 0
import matplotlib.pyplot as plt

def visualize_results(model, trainer, test_circuits_l, test_data_labels_l, acc):

    fig, ((ax_tl, ax_tr), (ax_bl, ax_br)) = plt.subplots(2, 2, sharex=True, sharey='row', figsize=(10, 6))
    ax_tl.set_title('Training set')
    ax_tr.set_title('Development set')
    ax_bl.set_xlabel('Iterations')
    ax_br.set_xlabel('Iterations')
    ax_bl.set_ylabel('Accuracy')
    ax_tl.set_ylabel('Loss')

    colours = iter(plt.rcParams['axes.prop_cycle'].by_key()['color'])
    ax_tl.plot(trainer.train_epoch_costs[::10], color=next(colours))
    ax_bl.plot(trainer.train_results['acc'][::10], color=next(colours))
    ax_tr.plot(trainer.val_costs[::10], color=next(colours))
    ax_br.plot(trainer.val_results['acc'][::10], color=next(colours))

    #for e in model(test_circuits_l):
    #    print(e)
    #for e in test_data_labels_l:
    #    print(e)

    # print test accuracy
    test_acc = acc(model(test_circuits_l), test_data_labels_l)
    print('Test accuracy:', test_acc)

def read_diagrams(circuit_paths):
    circuits = {}
    for serialized_diagram in circuit_paths:
        base_name = Path(serialized_diagram).stem
        f = open(serialized_diagram, "rb")
        diagram = pickle.load(f)
        circuits[base_name] = diagram
    return circuits


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
        
        
def normalise(predictions):
    # apply smoothing to predictions
    predictions = np.abs(predictions) + 1e-9
    return predictions / predictions.sum()
        

def create_labeled_classes(data, classification):
    labeled_data = {}
    sorted_data = sorted(data, key=lambda d: d['time'])
    chunk_size = math.ceil(len(sorted_data)/2**classification)
    for i, clas in enumerate(chunks(sorted_data, chunk_size)):
        label = [0]*(2**classification)
        label[i] = 1
        for elem in clas:
            labeled_data[elem["name"]] = label
    return labeled_data


def bin_class_acc(y_hat, y):
    y_hat = np.array(y_hat)
    y = np.array(y)
    return (np.sum(np.round(y_hat) == y) / len(y)) / 2


def bin_class_loss(y_hat, y):
    y_hat = np.array(y_hat)
    y = np.array(y)
    return -np.sum(y * np.log(y_hat)) / len(y)


def multi_class_acc(y_hat, y):
    total_acc = 0
    for pair in zip(y_hat, y):
        y_meas = np.array(pair[0]).flatten()
        max_index = np.argmax(y_meas)
        total_acc += int(int(pair[1][max_index]) == 1)
    return total_acc / len(y)


def multi_class_loss(y_hat, y):
    global i
    total_loss = 0
    if len(y_hat) != len(y):
        return 0
    for pair in zip(y_hat, y):
        x = pair[1]
        y_pred = np.array(pair[0]).flatten()
        #if i % 100 == 0:
        #    print(y_pred, x)
        if len(y_pred) != len(x):
            return 0
        total_loss += -np.sum(x * np.log(y_pred)) / len(x)
    i+=1
    return total_loss