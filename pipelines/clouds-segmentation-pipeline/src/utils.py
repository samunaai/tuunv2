import cv2
import numpy as np
import segmentation_models_pytorch as smp
import torch
import torch.nn as nn


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def single_dice_coef(y_pred_bin, y_true):
    if not isinstance(y_pred_bin, np.ndarray):
        y_pred_bin = y_pred_bin.cpu().detach().numpy()
    # y_pred_bin = sigmoid(y_pred_bin)
    # y_pred_bin = y_pred_bin > 0.5
    if not isinstance(y_true, np.ndarray):
        y_true = y_true.cpu().detach().numpy()
    intersection = np.sum(y_true * y_pred_bin)
    if (np.sum(y_true) == 0) and (np.sum(y_pred_bin) == 0):
        return 1
    return (2 * intersection) / (np.sum(y_true) + np.sum(y_pred_bin))


def mean_dice_coef(y_pred_bin, y_true, **kwargs):
    # shape of y_true and y_pred_bin: (n_samples, height, width, n_channels)
    # actual shape (Batch, channels, height, width)
    batch_size = y_true.shape[0]
    channel_num = y_true.shape[1]
    mean_dice_channel = 0.0
    for i in range(batch_size):
        for j in range(channel_num):
            channel_dice = single_dice_coef(y_pred_bin[i, j, :, :], y_true[i, j, :, :])
            mean_dice_channel += channel_dice
    mean_dice_channel /= channel_num * batch_size
    return mean_dice_channel


class DiceLoss(nn.Module):
    __name__ = "dice_loss"

    def __init__(self, eps=1e-7, activation="sigmoid"):
        super().__init__()
        self.activation = activation
        self.eps = eps

    def forward(self, y_pr, y_gt):
        return 1 - mean_dice_coef(y_pred_bin=y_pr, y_true=y_gt)


class BCEDiceLossCustom(DiceLoss):
    __name__ = "bce_dice_loss"

    def __init__(self, eps=1e-7, activation="sigmoid"):
        super().__init__(eps, activation)
        self.bce = nn.BCEWithLogitsLoss(reduction="mean")

    def forward(self, y_pr, y_gt):
        dice = super().forward(y_pr, y_gt)
        bce = self.bce(y_pr, y_gt)
        return dice + bce


def post_process(probability, threshold, min_size):
    """
    Post processing of each predicted mask, components with lesser number of pixels
    than `min_size` are ignored
    """
    # don't remember where I saw it
    mask = cv2.threshold(probability, threshold, 1, cv2.THRESH_BINARY)[1]
    num_component, component = cv2.connectedComponents(mask.astype(np.uint8))
    predictions = np.zeros((350, 525), np.float32)
    num = 0
    for c in range(1, num_component):
        p = component == c
        if p.sum() > min_size:
            predictions[p] = 1
            num += 1
    return predictions, num


def mask2rle(img):
    """
    Convert mask to rle.
    img: numpy array, 1 - mask, 0 - background
    Returns run length as string formated
    """
    pixels = img.T.flatten()
    pixels = np.concatenate([[0], pixels, [0]])
    runs = np.where(pixels[1:] != pixels[:-1])[0] + 1
    runs[1::2] -= runs[::2]
    return " ".join(str(x) for x in runs)
