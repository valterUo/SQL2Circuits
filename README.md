# Quantum natural language approach to SQL estimation

## SQL

The core idea of this implementation is heavily influenced by paper [A Quantum Natural Language Processing Approach to Musical Intelligence](https://arxiv.org/abs/2111.06741). The idea also roughly follows the pipeline described in [Lambeq documentation](https://cqcl.github.io/lambeq/pipeline.html).

1. SQL parser (based on SQLite syntax since it was easiest to make work in [ANTRL4](https://github.com/antlr))
2. Mapping the abstract syntax trees into context free grammar diagrams which are represented as string diagrams (contribution of this work)
3. Mapping the CFG diagrams functorially to pregroup grammars and representing them as string diagrams ([DisCoPy](https://github.com/oxford-quantum-group/discopy)) (mapping is contribution of this work and defined in pregroup_functor_data.json file)
4. Functorially rewriting pregroup diagrams to remove the cups and thus reduce the required number of qubits in the final result ([Snake removal example in DisCoPy](https://discopy.readthedocs.io/en/main/notebooks/snake-removal.html#))
5. Translating pregroup diagram representations into quantum circuits using [lambeq](https://github.com/CQCL/lambeq)

The obtained ansätze circuits are furthermore optimized with Lambeq's native QuantumTrainer and SPSA algorithm (same as in [A Quantum Natural Language Processing Approach to Musical Intelligence](https://arxiv.org/abs/2111.06741) and for example, see [Quanthoven](https://github.com/CQCL/Quanthoven/blob/main/experiment.ipynb). Instead of binary classification, we have multiple classes) and we also transform them into Pennylane which enables wide variety of other optimization approaches.

We believe that pregroup grammars and string diagrammas would theoretically allow transformations or comparisions between different query languages. Cypher does not have prewritten grammar among the [ANTRL4 grammars](https://github.com/antlr/grammars-v4) but it is offered on their website. The future research would include studying transformations between the various grammars taking into account the context that the databases provide.

## Cypher 

(possible TODO)