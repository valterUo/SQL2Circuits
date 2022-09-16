from typing import Callable
import warnings
import numpy as np
from qiskit.utils import algorithm_globals
import math

def bernoulli_perturbation(dim, perturbation_dims=None):
    """Get a Bernoulli random perturbation."""
    if perturbation_dims is None:
        return 1 - 2 * algorithm_globals.random.binomial(1, 0.5, size=dim)

    pert = 1 - 2 * algorithm_globals.random.binomial(1, 0.5, size=perturbation_dims)
    indices = algorithm_globals.random.choice(
        list(range(dim)), size=perturbation_dims, replace=False
    )
    result = np.zeros(dim)
    result[indices] = pert

    return result


def magnitude(number):
    return math.floor(math.log(number, 10))
        
def calibrate(loss: Callable[[np.ndarray], float], 
              initial_point: np.ndarray, 
              c: float = 0.2, 
              A: float = 0, 
              alpha: float = 0.602, 
              gamma: float = 0.101):

        dim = len(initial_point)

        # compute the average magnitude of the first step
        steps = 25
        points = []
        for _ in range(steps):
            # compute the random directon
            pert = bernoulli_perturbation(dim)
            points += [initial_point + c * pert, initial_point - c * pert]
            
        losses = [-np.sum(point * np.log(initial_point))/len(point) for point in points]
        avg_magnitudes = 0
        for i in range(steps):
            delta = losses[2 * i] - losses[2 * i + 1]
            avg_magnitudes += np.abs(delta / (2 * c))

        avg_magnitudes /= steps
        
        a = (((A + 1)**(alpha))*magnitude(c))/magnitude(avg_magnitudes)

        # compute the rescaling factor for correct first learning rate
        if a < 1e-10:
            warnings.warn(f"Calibration failed, using {target_magnitude} for `a`")
            a = target_magnitude

        print(f" -- Learning rate: a / ((A + n) ^ alpha) with a = {a}, A = {A}, alpha = {alpha}")
        print(f" -- Perturbation: c / (n ^ gamma) with c = {c}, gamma = {gamma}")

        return a, c