import hydra
from omegaconf import DictConfig

from src.postprocess import postprocess
from src.preprocess import preprocess
from src.train import train
import wandb
import datetime


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
    preprocess_time = preprocess(cfg=cfg)
    dice_score = train(cfg=cfg)
    # postprocess(cfg=cfg)
    wandb.log({'preprocess time': preprocess_time, 'dice score': dice_score})



if __name__ == "__main__":
    run()
