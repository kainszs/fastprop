import os
import pickle

import numpy as np
import pandas as pd
import yaml
from rdkit import Chem
from glob import glob

from fastprop.defaults import init_logger
from fastprop.utils import calculate_mordred_desciptors
from fastprop.utils.select_descriptors import mordred_descriptors_from_strings

from .fastprop_core import fastprop

logger = init_logger(__name__)


def _safe_yaml_open(dir, fname):
    try:
        with open(os.path.join(dir, fname)) as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.error(f"checkpoints directory is missing '{fname}'. Re-execute training.")


def predict_fastprop(checkpoints_dir, smiles, input_file, output:str=None):
    """Prediction CLI.

    Loads a model and runs inference on the input.

    Args:
        checkpoints_dir (str): 'checkpoints' directory from a previous fastprop train.
        smiles (str or list[str]): SMILES strings for prediction.
        input_file (str): Input file containing only SMILES strings for prediction.
        output (str or None): Either save to a file or just print result.
    """

    if type(smiles) is str:
        smiles = [smiles]
    
    if input_file is not None:
        smiles = pd.read_csv(input_file)["smiles"].tolist()
    
    checkpoint_dir_contents = os.listdir(checkpoints_dir)

    config_dict = _safe_yaml_open(checkpoints_dir, "fastprop_config.yml")
    descs = calculate_mordred_desciptors(
        mordred_descriptors_from_strings(config_dict["descriptors"]),
        [Chem.MolFromSmiles(i) for i in smiles],
        n_procs=0,  # ignored for "strategy='low-memory'"
        strategy="low-memory",
    )

    all_models = [s for s in checkpoint_dir_contents if s.endswith(".ckpt")]

    # select the latest checkpoint
    checkpoint = sorted(all_models, key=lambda s: s.split("-")[-1])[-1]

    model = fastprop.load_from_checkpoint(
        os.path.join(checkpoints_dir, checkpoint),
        cleaned_data=None,
        targets=None,
        smiles=None,
    )
    scalers = _safe_yaml_open(checkpoints_dir, f"repetition_{checkpoint.split('-')[1]}_scalers.yml")
    model.target_scaler = pickle.loads(scalers["target_scaler"])
    model.mean_imputer = pickle.loads(scalers["mean_imputer"])
    model.feature_scaler = pickle.loads(scalers["feature_scaler"])

    # axis: contents
    # 0: smiles
    # 1: predictions
    # 2: per-model

    prediction = model.predict_step(descs)

    result = pd.DataFrame(
        {
            "smiles": smiles,
            "logS": prediction.flatten(),
        }
    )

    result.to_csv(output, index=False)
