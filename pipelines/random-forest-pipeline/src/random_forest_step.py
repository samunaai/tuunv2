from hydra.utils import get_original_cwd
from omegaconf import DictConfig

from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from src.data_utils import *
 
import numpy as np  
import os
import pandas as pd
import scipy.sparse
import time


def train_model(cfg: DictConfig):
	start_time = time.time()
	_, _, y_train, y_test = get_train_test_split(os.path.join(get_original_cwd(), cfg.data_in), cfg.test_size)
	
	feat_indir = os.path.join(get_original_cwd(), cfg.feat_outdir); 

	X_feats_train = scipy.sparse.load_npz(os.path.join(feat_indir, "feats_train.npz"))
	X_feats_test = scipy.sparse.load_npz(os.path.join(feat_indir, "feats_test.npz"))

	print("(2) ==>", X_feats_train.shape, X_feats_test.shape)
 
	classifier = Pipeline([ 
	    ('classifier', RandomForestClassifier(min_samples_leaf=cfg.min_samples_leaf, 
	    							max_depth=cfg.max_depth, random_state=cfg.random_seed)),
	])
	
	classifier.fit(X_feats_train, y_train)
 
	preds = classifier.predict(X_feats_test)

	final_score = np.mean(preds == y_test)
	
	return final_score, time.time() - start_time