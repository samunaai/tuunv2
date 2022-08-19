import datetime

import hydra
from omegaconf import DictConfig

from src.feature_extraction_step import vectorizer
from src.random_forest_step import train_model


@hydra.main(config_path="configs", config_name="config.yaml")
def run(cfg: DictConfig): 

	if cfg.action == "vectorize":
		preprocess_time = vectorizer(cfg=cfg)
	elif cfg.action == "model":
		train_score, train_time = train_model(cfg=cfg)
		print("\n\n[TuunV2] Final Score =>", train_score)
	else:
		print("\n\n\t\t[TuunV2] -> *** ERROR: Action Must Be 'vectorize', or 'model'! \n\n")
    

if __name__ == "__main__":
    run()
