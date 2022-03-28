# Quantum computing for database query languages

This repository will contain the following implementations in near future. The idea is heavily influenced by paper [A Quantum Natural Language Processing Approach to Musical Intelligence](https://arxiv.org/abs/2111.06741).

1. SQL parser (based on SQLite syntax since it was easiest to make work in [ANTRL4](https://github.com/antlr))
2. Mapping the abstract syntax trees into context free grammar diagrams (own contribution)
3. Mapping the CFG functorially to pregroup grammars and representing them as string diagrams ([DisCoPy](https://github.com/oxford-quantum-group/discopy))
4. Translating string diagram representations into quantum circuits ([lambeq](https://github.com/CQCL/lambeq))
5. Figure out how to utilize the parametrized circuit. For example, see [Quanthoven](https://github.com/CQCL/Quanthoven/blob/main/experiment.ipynb).

Pregroup grammars and string diagrammas would theoretically allow transformations or comparisions between different query languages. Unfortunately, Cypher does not have prewritten grammar among the [ANTRL4 grammars](https://github.com/antlr/grammars-v4). There might be some fast way to translate existing openCypher grammars into .g4 lexer and parser files, maybe...