import os

import numpy as np
import pandas as pd
import segmentation_models_pytorch as smp
import torch
from hydra.utils import get_original_cwd
from omegaconf import DictConfig
from sklearn.model_selection import train_test_split
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader
from tqdm import tqdm

from src.dataset import CloudDataset
from src.transforms import get_preprocessing, get_train_aug, get_valid_aug
from src.utils import BCEDiceLossCustom, dice_no_threshold


def train(cfg: DictConfig):
    df_train = pd.read_csv(os.path.join(get_original_cwd(), cfg.data_path, "train.csv"))
    model = smp.Unet(
        encoder_name=cfg.encoder,
        encoder_weights="imagenet",
        classes=4,
        activation=None,
    ).cuda()
    preprocessing_fn = smp.encoders.get_preprocessing_fn(cfg.encoder, "imagenet")

    id_mask_count = (
        df_train.loc[df_train["EncodedPixels"].isnull() == False, "Image_Label"]
        .apply(lambda x: x.split("_")[0])
        .value_counts()
        .reset_index()
        .rename(columns={"index": "img_id", "Image_Label": "count"})
    )
    train_ids, valid_ids = train_test_split(
        id_mask_count["img_id"].values,
        random_state=42,
        stratify=id_mask_count["count"],
        test_size=0.25,
    )

    train_dataset = CloudDataset(
        df=df_train,
        cfg=cfg,
        img_ids=train_ids,
        transforms=get_train_aug(),
        preprocessing=get_preprocessing(preprocessing_fn),
    )
    valid_dataset = CloudDataset(
        df=df_train,
        cfg=cfg,
        img_ids=valid_ids,
        transforms=get_valid_aug(),
        preprocessing=get_preprocessing(preprocessing_fn),
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=cfg.batch_size,
        shuffle=True,
        num_workers=cfg.num_workers,
    )
    valid_loader = DataLoader(
        valid_dataset,
        batch_size=cfg.batch_size,
        shuffle=False,
        num_workers=cfg.num_workers,
    )

    optimizer = torch.optim.Adam(
        [
            {"params": model.decoder.parameters(), "lr": cfg.lr_decoder},
            {"params": model.encoder.parameters(), "lr": cfg.lr_encoder},
        ]
    )
    scheduler = ReduceLROnPlateau(optimizer, factor=0.15, patience=2)
    criterion = BCEDiceLossCustom()

    train_loss_list = []
    valid_loss_list = []
    dice_score_list = []
    lr_rate_list = []
    valid_loss_min = np.Inf  # track change in validation loss
    for epoch in range(1, cfg.epochs + 1):

        train_loss = 0.0
        valid_loss = 0.0
        dice_score = 0.0

        model.train()
        bar = tqdm(train_loader, postfix={"train_loss": 0.0})
        for data, target in bar:
            data, target = data.cuda(), target.cuda()
            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * data.size(0)
            bar.set_postfix(ordered_dict={"train_loss": loss.item()})

        model.eval()
        del data, target
        with torch.no_grad():
            bar = tqdm(valid_loader, postfix={"valid_loss": 0.0, "dice_score": 0.0})
            for data, target in bar:
                data, target = data.cuda(), target.cuda()
                output = model(data)
                loss = criterion(output, target)
                valid_loss += loss.item() * data.size(0)
                dice_cof = dice_no_threshold(output.cpu(), target.cpu()).item()
                dice_score += dice_cof * data.size(0)
                bar.set_postfix(
                    ordered_dict={"valid_loss": loss.item(), "dice_score": dice_cof}
                )

        train_loss = train_loss / len(train_loader.dataset)
        valid_loss = valid_loss / len(valid_loader.dataset)
        dice_score = dice_score / len(valid_loader.dataset)
        train_loss_list.append(train_loss)
        valid_loss_list.append(valid_loss)
        dice_score_list.append(dice_score)
        lr_rate_list.append(
            [param_group["lr"] for param_group in optimizer.param_groups]
        )

        print(
            "Epoch: {}  Training Loss: {:.6f}  Validation Loss: {:.6f} Dice Score: {:.6f}".format(
                epoch, train_loss, valid_loss, dice_score
            )
        )

        if valid_loss <= valid_loss_min:
            print(
                "Validation loss decreased ({:.6f} --> {:.6f}).  Saving model ...".format(
                    valid_loss_min, valid_loss
                )
            )
            torch.save(
                {"state_dict": model.state_dict()},
                os.path.join(get_original_cwd(), cfg.checkpoint_dir, "best.pth"),
            )
            valid_loss_min = valid_loss
        scheduler.step(valid_loss)
    return max(dice_score_list)