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
        test_size=cfg.test_size,
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

    encoded_pixels = []
    pred_distr = {-1: 0, 0: 0, 1: 0, 2: 0, 3: 0}
    image_id = 0
    model.eval()

    dices = []
    with torch.no_grad():
        for images, labels in tqdm.tqdm(valid_loader, total=len(valid_loader)):
            masks = model(images)
            for mask, label in zip(masks, labels):
                mask = mask.cpu().detach().numpy()
                if mask.shape != (350, 525):
                    mask = cv2.resize(
                        mask, dsize=(525, 350), interpolation=cv2.INTER_LINEAR
                    )
                mask, num_predict = post_process(
                    sigmoid(mask),
                    cfg.threshold,
                    cfg.min_mask_size,
                )

                dices.append(dice(mask, label))
                if num_predict == 0:
                    pred_distr[-1] += 1
                    encoded_pixels.append("")
                else:
                    pred_distr[image_id % 4] += 1
                    r = mask2rle(mask)
                    encoded_pixels.append(r)
                image_id += 1

    print(
        f"empty={pred_distr[-1]} fish={pred_distr[0]} flower={pred_distr[1]} gravel={pred_distr[2]} sugar={pred_distr[3]}"
    )
    non_empty = pred_distr[0] + pred_distr[1] + pred_distr[2] + pred_distr[3]
    all = non_empty + pred_distr[-1]
    sub = pd.read_csv(f"./artifacts/sample_submission.csv")
    sub["EncodedPixels"] = encoded_pixels
    sub.to_csv(
        f"submission.csv",
        columns=["Image_Label", "EncodedPixels"],
        index=False,
    )
    # todo compute dice
