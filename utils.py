from pathlib import Path
import pickle
import math
import numpy as np

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


def acc(y_hat, y):
    y_hat = np.array(y_hat).flatten()
    y = np.array(y).flatten()
    return (np.sum(np.round(y_hat) == y) / len(y)) / 2


def loss(y_hat, y):
    y_hat = np.array(y_hat).flatten()
    y = np.array(y).flatten()
    return -np.sum(y * np.log(y_hat)) / len(y)