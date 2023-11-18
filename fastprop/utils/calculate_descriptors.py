from mordred import Calculator
import numpy as np
from typing import Literal
from multiprocessing import Pool


# mordred tried to avoid instantiating multiple Calculator classes, which makes
# the parallelism slower but more memory efficient. We do this manually:
def _f(in_tuple):
    mordred_calc = Calculator(in_tuple[2], ignore_3D=True)
    mordred_descs = np.array(list(mordred_calc.map(in_tuple[0], nproc=1, quiet=in_tuple[1])))
    return mordred_descs


def calculate_mordred_desciptors(descriptors, rdkit_mols, n_procs, strategy: Literal["fast", "low-memory"] = "fast"):
    # descriptors should be a list of mordred descriptors classes
    if strategy not in {"fast", "low-memory"}:
        raise RuntimeError(f"Strategy {strategy} not supported, only 'fast' and 'low-memory'.")

    mordred_descs = None
    if strategy == "fast":
        # higher level parallelism - uses more memory
        batches = np.array_split(rdkit_mols, n_procs)
        # let the root process show a progress bar, since array split will make
        # that one the largest
        to_procs = [(batch, bool(i), descriptors) for i, batch in enumerate(batches)]
        with Pool(n_procs) as p:
            mordred_descs = np.vstack(p.map(_f, to_procs, 1))
    else:
        # mordred parallelism
        mordred_calc = Calculator(descriptors, ignore_3D=True)
        mordred_descs = np.array(list(mordred_calc.map(rdkit_mols, nproc=n_procs, quiet=False)))
    return mordred_descs