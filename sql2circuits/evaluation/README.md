# Evaluation module

This module implements the following workflow which evaluates SQL2Circuits model:

3. Evaluation on a static database
    1. Cross validation    
4. Evaluation on a dynamic database
    1. Database that has been updated without modifications to schema
    2. Database that has been updated with modifications to schema
    3. Evaluation on queries with not-seen-before parameters
5. Classical evaluation (See if there are any existing implementations)
    1. Histograms
    2. Sketches
    3. Sampling
    4. PostgreSQL's native estimator
    5. Machine learning-based methods


For each evaluation round, we can consider that we can run the model in different platforms:
1. Queries: static or dynamic set of queries
2. Database which matches the queries: static or dynamic
3. Trained model i.e. the correct parameters
4. Quantum backend i.e. device:
    1. Simulators
        1. Exact classical locally
        2. Qiskit Aer simulator
        3. Lumi supercomputer
    2. Real hardware ?
        1. Helmi quantum computer ?
        2. IBM Quantum ?
        3. Xanadu Cloud ?