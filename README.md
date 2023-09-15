# SQL2Circuits: Estimating Metrics for SQL Queries with A Quantum Natural Language Processing Method

## Example

1. The user has a fixed relational database
2. The user wants to estimate the execution time / cardinality / cost of a query
3. The SQL2Circuits framework estimates the metrics with quantum circuits with the following pipeline
    1. The SQL query is parsed into an abstract syntax tree which is represented with a context-free grammar diagram
    2. The context-free grammar diagram is mapped functorially to a pregroup grammar diagram
    3. The pregroup grammar diagram is mapped functorially to a parametrized quantum circuit
    4. The system utilizes various classical optimization methods to tune the parameters of the quantum circuit so that the measurement result of the circuit corresponds to a classification which estimates the wanted database metric
4. The user and the database can use the estimated metric to optimize the query further

## Introduction

The core idea of this implementation is heavily influenced by paper [A Quantum Natural Language Processing Approach to Musical Intelligence](https://arxiv.org/abs/2111.06741). The implementation roughly follows the pipeline described in [Lambeq documentation](https://cqcl.github.io/lambeq/pipeline.html).

1. SQL parser (based on SQLite syntax since it was easiest to make work in [ANTRL4](https://github.com/antlr))
2. Mapping the abstract syntax trees into context-free grammar diagrams which are represented as string diagrams (contribution of this work)
3. Mapping the CFG diagrams functorially to pregroup grammars diagrams ([DisCoPy](https://github.com/oxford-quantum-group/discopy)) (mapping is contribution of this work and defined in pregroup_functor_data.json file)
4. Functorially rewriting pregroup diagrams to remove the cups and thus reduce the required number of qubits and post-processing in the final circuit ([Snake removal example in DisCoPy](https://discopy.readthedocs.io/en/main/notebooks/snake-removal.html#))
5. Translating cupless pregroup diagrams into quantum circuits using [lambeq](https://github.com/CQCL/lambeq) and IQPansatz
6. Optimize the circuits to make predictions about SQL queries with SPSA algorithm

The obtained ansätze are furthermore optimized with Lambeq's native QuantumTrainer and SPSA algorithm (similarly as in [A Quantum Natural Language Processing Approach to Musical Intelligence](https://arxiv.org/abs/2111.06741) and for example, see [Quanthoven](https://github.com/CQCL/Quanthoven/blob/main/experiment.ipynb). Instead of binary classification, we have multiple classes and we also transform them into Pennylane which enables wide variety of other optimization approaches.

## How to reproduce the results

1. Download the dump files containing the IMDB database from [here]().
2. Create the IMDB database with the dump files.
3. Clone this repository and install the requirements. Note the required versions of the packages.
4. Run the `main.py` file with the desired parameters. The possible parameter values are described in the `sql2circuits_config.json` file.
5. Depending on the selected parameters, the following quantum machine learning training pipeline will be executed:
    1. The training, validation and test queries are generated based on the query seed file provided.
    2. The queries are executed on PostgreSQL database and depending on the initial configuration, either the execution time, cardinality or cost is measured.
    3. The SQL queries are parsed into abstract syntax trees and mapped into parametrized quantum circuits.
    4. The circuits are optimized with the selected classical algorithm. The optimization is performed iteratively: we first optimize a batch of circuits and then add more depending on the parameters we defined initially.
    5. The results are saved in the `results` folder.


## Cypher 

TODO

We believe that pregroup grammars and string diagrammas would theoretically allow transformations or comparisions between different query languages. Cypher does not have prewritten grammar among the [ANTRL4 grammars](https://github.com/antlr/grammars-v4) but it is offered on their website. The future research would include studying transformations between the various grammars taking into account the context that the databases provide.
