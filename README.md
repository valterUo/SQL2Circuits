# SQL2Circuits: Estimating Metrics for SQL Queries with A Quantum Natural Language Processing Method

On-going work!

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
0. You can create your own queries and later in the code correct the paths to point to the queries. Note that SQL queries need to be conjunctive SELECT-FROM-WHERE type of queries without subqueries. For example, the queries in Join Order Benchmark follow the requirements.
1. Create and initialize PostgreSQL database with IMDB dataset. This will be used to collect the training data.
    1. Follow PostgreSQL installation guidelines at PostgreSQL
    2. Execute the correct CREATE DATABASE command from IMDBtoPostgresCommand.txt file:
    ```
    CREATE DATABASE imdb2017
    WITH OWNER postgres
    TEMPLATE = template0
    ENCODING UTF8
    LC_COLLATE = 'und-x-icu'
    LC_CTYPE = 'und-x-icu';
    ```
    If the database does not have correct template and encoding, the IMDB will not be initialized correctly.
    3. Execute `data_generator.ipynb` Jupyter notebook. This notebook will initialize IMDB database with the old data from year 2017. Link to the dataset can be found from [Cinemagoer documentation](https://cinemagoer.readthedocs.io/en/latest/usage/ptdf.html) and you need to input the correct database credentials in the notebook. Since the data will not be modified in the database, you need to perform this step only once.
    4. The notebook will create training, validation and test data depending on the paths you have defined in the notebook. You can decide which queries you want to use and modify the paths.
2. Install required packages: DisCoPy, Lambeq, ANTRL4, Pennylane, etc. To speed up training we use JAX as described in [Quanthoven](https://github.com/CQCL/Quanthoven/blob/main/experiment.ipynb).
3. Construct circuits from the queries by running `sql_to_circuit_ansatze.ipynb`. The notebook creates a bunch of diagrams in parallel. It serializes the diagrams as JSON files and stores them also as PNG images. Circuits are also stored as pickled python files since they will be accessed in the second phase.
4. Execute any of the notebooks with name starting `circuit_learning_with_`. In the end of the notebooks you will obtain the results.

Notebook execution order:
1. In the case you want your own query set: `query_generator.ipynb`
2. Generate data: `data_generator.ipynb`
3. Construct circuits from the queries: `sql_to_circuit_ansatze.ipynb`
4. Any of the following to optimize the parameters in the circuits:
    1. `circuit_learning_with_Lambeq_SPSA_manual_with_jax.ipynb`
    2. `circuit_learning_with_Lambeq_SPSA_QuantumTrainer_with_jax.ipynb` 
    3. `circuit_learning_with_Pennylane_gradient.ipynb`
    4. `circuit_learning_with_Pennylane_SPSA.ipynb`

## Cypher 

TODO

We believe that pregroup grammars and string diagrammas would theoretically allow transformations or comparisions between different query languages. Cypher does not have prewritten grammar among the [ANTRL4 grammars](https://github.com/antlr/grammars-v4) but it is offered on their website. The future research would include studying transformations between the various grammars taking into account the context that the databases provide.
