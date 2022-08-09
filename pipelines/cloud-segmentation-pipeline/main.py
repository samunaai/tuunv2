import datetime

import hydra
import wandb
from omegaconf import DictConfig

from src.postprocess import postprocess
from src.preprocess import preprocess
from src.train import train


@hydra.main(config_path="configs", config_name="config.yaml")
def run(cfg: DictConfig):
	name = datetime.datetime.now().strftime("%b%d_%H:%M:%S")
	run = None
	if cfg.log_wandb:
		run = wandb.init(
		    project="cloud-segmentation-pipeline",
		    name=name,
		    entity="tuunv2",
		    config=cfg,
		    # mode="disabled" if cfg.debug == "local" else "online",
		)

	if cfg.action == "preprocess":
		preprocess_time = preprocess(cfg=cfg)
		if cfg.log_wandb:
			run.log({'preprocessing time': preprocessd_time})  
	elif cfg.action == "train":
		train_dice_score, train_time = train(cfg=cfg, run=run)
		if cfg.log_wandb:
			run.log({"max train dice score": train_dice_score, "train time": train_time})
	elif cfg.action == "postprocess":
		final_dice, postprocess_time = postprocess(cfg=cfg)
		if cfg.log_wandb:
			run.log({"dice after postprocessing": final_dice, "postprocessing time": postprocess_time})
			run.finish()
		print("\n\n [TuunV2] Final Dice Score =>", final_dice)
	else:
		print("\n\n \t\t [TuunV2] -> *** ERROR: Action Must Be 'preprocess', 'train', or 'postprocess'! \n\n")
    

    

if __name__ == "__main__":
    run()
