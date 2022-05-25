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
    run = wandb.init(
        project="cloud-segmentation-pipeline",
        name=name,
        entity="cyr1ll",
        config=cfg,
        mode="disabled" if cfg.debug == "local" else "online",
    )

   # preprocess_time = preprocess(cfg=cfg)
   # run.log({'preprocessing time': preprocess_time})

    train_dice_score, train_time = train(cfg=cfg, run=run)
    run.log({"max train dice score": train_dice_score, "train time": train_time})

    final_dice = postprocess(cfg=cfg)
    run.log({"dice after postprocessing": final_dice})
    
    run.finish()


if __name__ == "__main__":
    run()
