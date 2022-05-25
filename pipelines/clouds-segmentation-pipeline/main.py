import datetime

import hydra
import wandb
from omegaconf import DictConfig

from src.postprocess import postprocess
from src.preprocess import preprocess
from src.train import train


@hydra.main(config_path="configs", config_name="config.yaml")
def run(cfg: DictConfig):
    name = str(datetime.datetime.now())
    wandb.init(
        project="cloud-segmentation-pipeline",
        name=name,
        entity="cyr1ll",
        config=cfg,
        mode="disabled" if cfg.debug == "local" else "online",
    )

    # preprocess_time = preprocess(cfg=cfg)
    # wandb.log({'preprocess time': preprocess_time})

    train_dice_score, time = train(cfg=cfg)
    wandb.log({"train time": train_dice_score})

    final_dice = postprocess(cfg=cfg)
    wandb.log({"final dice": final_dice})


if __name__ == "__main__":
    run()
