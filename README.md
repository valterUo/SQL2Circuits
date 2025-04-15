# SQL2Circuits: Estimating Cardinalities, Execution Times, and Costs for SQL Queries with Quantum Natural Language Processing

## Example

1. The user has a fixed relational database and wants to estimate the execution time / cardinality / cost of a query
3. The SQL2Circuits framework estimates the metrics with quantum circuits with the following pipeline
    1. The SQL query is parsed into an abstract syntax tree which is represented with a context-free grammar diagram
    2. The context-free grammar diagram is mapped functorially to a pregroup grammar diagram
    3. The pregroup grammar diagram is mapped functorially to a parametrized quantum circuit
    4. The system utilizes various classical optimization methods to tune the parameters of the quantum circuit so that the measurement result of the circuit corresponds to a classification which estimates the wanted database metric
4. The user and the database can use the estimated metric to optimize the query further

## Introduction

The core idea of this implementation is influenced by [Quantum natural language processing](https://arxiv.org/abs/2102.12846). The implementation roughly follows the pipeline described in [Lambeq documentation](https://cqcl.github.io/lambeq/pipeline.html). There is a lot more related work on quantum natural language processing.

### Some technical details

1. SQL parser (based on SQLite syntax since it was easiest to make work in [ANTRL4](https://github.com/antlr))
2. Mapping the abstract syntax trees into context-free grammar diagrams which are represented as string diagrams (contribution of this work)
3. Mapping the CFG diagrams functorially to pregroup grammars diagrams ([DisCoPy](https://github.com/oxford-quantum-group/discopy)) (mapping is contribution of this work and defined in pregroup_functor_data.json file)
4. Functorially rewriting pregroup diagrams to remove the cups and thus reduce the required number of qubits and post-processing in the final circuit ([Snake removal example in DisCoPy](https://discopy.readthedocs.io/en/main/notebooks/snake-removal.html#))
5. Translating cupless pregroup diagrams into quantum circuits using [lambeq](https://github.com/CQCL/lambeq) and IQPansatz
6. Optimize the circuits to make predictions about SQL queries with SPSA and Adam optimizers

## How to reproduce the results

1. Download and create the IMDB database as described in [Join Order Benchmark](https://github.com/gregrahn/join-order-benchmark).
3. Clone this repository and install the requirements. Note the required versions of the packages.
4. Run the `main.py` file with the desired parameters. The possible parameter values are described in the `sql2circuits_config.json` file.
5. Depending on the selected parameters, the following quantum machine learning training pipeline will be executed:
    1. The training, validation and test queries are generated based on the query seed file provided.
    2. The queries are executed on PostgreSQL database and depending on the initial configuration, either the execution time, cardinality or cost is measured.
    3. The SQL queries are parsed into abstract syntax trees and mapped into parametrized quantum circuits.
    4. The circuits are optimized with the selected classical algorithm. The optimization is performed iteratively: we first optimize a batch of circuits and then add more depending on the parameters we defined initially.
    5. The results are saved in the `results` folder.
