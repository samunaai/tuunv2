import os

import cv2
import numpy as np
import pandas as pd
import segmentation_models_pytorch as smp
import torch
import tqdm
from hydra.utils import get_original_cwd
from omegaconf import DictConfig
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader

from src.dataset import CloudDataset
from src.transforms import get_preprocessing, get_valid_aug
from src.utils import mask2rle, post_process, sigmoid


def postprocess(cfg: DictConfig):
    df_train = pd.read_csv(os.path.join(get_original_cwd(), cfg.data_path, "train.csv"))
    model = smp.Unet(
        encoder_name=cfg.encoder,
        encoder_weights="imagenet",
        classes=4,
        activation=None,
    ).cuda()
    model.load_state_dict(
        torch.load(os.path.join(get_original_cwd(), cfg.checkpoint_dir, "best.pth"))[
            "state_dict"
        ]
    )
    model.eval()

    id_mask_count = (
        df_train.loc[df_train["EncodedPixels"].isnull() == False, "Image_Label"]
        .apply(lambda x: x.split("_")[0])
        .value_counts()
        .reset_index()
        .rename(columns={"index": "img_id", "Image_Label": "count"})
    )
    _, valid_ids = train_test_split(
        id_mask_count["img_id"].values,
        random_state=42,
        stratify=id_mask_count["count"],
        test_size=0.25,
    )
    preprocessing_fn = smp.encoders.get_preprocessing_fn(cfg.encoder, "imagenet")
    valid_dataset = CloudDataset(
        df=df_train,
        cfg=cfg,
        img_ids=valid_ids,
        transforms=get_valid_aug(),
        preprocessing=get_preprocessing(preprocessing_fn),
    )
    valid_loader = DataLoader(
        valid_dataset,
        batch_size=cfg.batch_size,
        shuffle=False,
        num_workers=cfg.num_workers,
    )
    encoded_pixels = []
    image_id = 0

    for data, target in tqdm(valid_loader):
        output = model(data)
        for i, batch in enumerate(output):
            for probability in batch:
                probability = probability.cpu().detach().numpy()
                if probability.shape != (350, 525):
                    probability = cv2.resize(
                        probability, dsize=(525, 350), interpolation=cv2.INTER_LINEAR
                    )
                predict, num_predict = post_process(
                    sigmoid(probability), cfg.threshold, cfg.min_mask_size
                )
                if num_predict == 0:
                    encoded_pixels.append("")
                else:
                    r = mask2rle(predict)
                    encoded_pixels.append(r)
                image_id += 1
    # todo compute dice
