from hydra.utils import get_original_cwd
from omegaconf import DictConfig

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from src.data_utils import *

import os
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import scipy.sparse
import time
  
 
class TextSelector(BaseEstimator, TransformerMixin):
    """
    Transformer to select a single column from the data frame to perform additional transformations on
    Use on text columns in the data
    """
    def __init__(self, key):
        self.key = key

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X[self.key] 


def vectorizer(cfg: DictConfig):
	start_time = time.time()
	X_train, X_test, _, _= get_train_test_split(os.path.join(get_original_cwd(), cfg.data_in), cfg.test_size)

	feature_extractor = Pipeline([
	                ('selector', TextSelector(key='processed')),
	                ('tfidf', TfidfVectorizer( stop_words='english', max_df=cfg.max_df, ngram_range=cfg.ngram_range ))
	            ])

	feature_extractor.fit(X_train)
	
	X_feats_train = feature_extractor.transform(X_train)
	X_feats_test = feature_extractor.transform(X_test)
	
	print("(0) ==>", X_feats_train.shape, X_train.shape)
	print("(1) ==>", X_feats_test.shape, X_test.shape)

	feat_outdir = os.path.join(get_original_cwd(), cfg.feat_outdir); os.makedirs(feat_outdir, exist_ok=True); 
 
	scipy.sparse.save_npz(os.path.join(feat_outdir, "feats_train.npz"), X_feats_train)
	scipy.sparse.save_npz(os.path.join(feat_outdir, "feats_test.npz"), X_feats_test)
	
	return time.time() - start_time