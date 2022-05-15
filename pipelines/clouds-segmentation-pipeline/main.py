import hydra
from omegaconf import DictConfig

from src.postprocess import postprocess
from src.preprocess import preprocess
from src.train import train


@hydra.main(config_path="configs", config_name="config.yaml")
def run(cfg: DictConfig):
    # preprocess(cfg=cfg)
    train(cfg=cfg)
    # postprocess(cfg=cfg)


if __name__ == "__main__":
    run()
