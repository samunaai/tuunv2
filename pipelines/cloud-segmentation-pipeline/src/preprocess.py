import cv2
import numpy as np
import nvidia.dali.fn as fn
import os
import pandas as pd
import time

from hydra.utils import get_original_cwd
from nvidia import dali
from nvidia.dali import pipeline_def
from omegaconf import DictConfig
from tqdm import tqdm
from typing import List


@pipeline_def
def image_resizing_pipeline(
    file_names: List[str], height_out: int, width_out: int, device: str
):
    """Dali based image resizing pipeline"""
    jpegs, _ = fn.readers.file(files=file_names)
    if device == "gpu":
        images = fn.decoders.image(jpegs, device="mixed")  # cpu, mixed
        images = fn.resize(images.gpu(), size=[height_out, width_out], device="gpu")
    else:
        images = fn.decoders.image(jpegs, device="cpu")  # cpu, mixed
        images = fn.resize(images, size=[height_out, width_out], device="cpu")
    return images

def mask2rle(img):
    '''
    Convert mask to rle.
    img: numpy array, 1 - mask, 0 - background
    Returns run length as string formated
    citation: https://www.kaggle.com/code/phunghieu/dataset-preparation-resize-images
    '''
    pixels= img.T.flatten()
    pixels = np.concatenate([[0], pixels, [0]])
    runs = np.where(pixels[1:] != pixels[:-1])[0] + 1
    runs[1::2] -= runs[::2]
    return ' '.join(str(x) for x in runs)

def rle2mask(mask_rle, shape):
    """
    mask_rle: run-length as string formatted (start length)
    shape: (width,height) of array to return
    Returns numpy array, 1 - mask, 0 - background
    citation: https://www.kaggle.com/code/phunghieu/dataset-preparation-resize-images
    """
    s = mask_rle.split()
    starts, lengths = [np.asarray(x, dtype=int) for x in
                       (s[0:][::2], s[1:][::2])]
    starts -= 1
    ends = starts + lengths
    img = np.zeros(shape[0] * shape[1], dtype=np.uint8)
    for lo, hi in zip(starts, ends):
        img[lo:hi] = 1
    return img.reshape(shape).T

def resize_masks(cfg: DictConfig):
    """Loads the masks to RAM from csv, resizes, and writes new csv to disk
    Masks are not saved in disk.
    """
    # load the mask csv
    train_df = pd.read_csv(os.path.join(get_original_cwd(), cfg.masks_csv_in))
    train_df["label"] = train_df["Image_Label"].apply(lambda x: x.split("_")[1])
    train_df["im_id"] = train_df["Image_Label"].apply(lambda x: x.split("_")[0])
    
    ori_size = cfg.ori_size
    new_size = (cfg.resize_height, cfg.resize_width)

    # convert masks from csv to array, resize, and modify csv
    for idx, row in train_df.iterrows():
        encodedpixels = row[1]
        if encodedpixels is not np.nan:
            mask = rle2mask(encodedpixels, shape=ori_size[::-1])
            mask = cv2.resize(mask, new_size[::-1], interpolation=cv2.INTER_CUBIC)

            rle = mask2rle(mask)
            train_df.at[idx, 'EncodedPixels'] = rle
    # make the directory to store new csv        
    out_csv = os.path.join(get_original_cwd(), cfg.masks_csv_out) 
    # write segs to new csv after resize   
    train_df.to_csv(out_csv, index=False)
    return out_csv

def preprocess(cfg: DictConfig):
    """
    This function performs preprocessing operations for images & masks !
    """
    time_start = time.time()

    # setting the needed directories using relative paths
    image_in_dir = os.path.join(get_original_cwd(), cfg.images_dir_in)
    image_out_dir = os.path.join(get_original_cwd(), cfg.image_dir_out)


    # make the output directory for the output images
    os.makedirs(image_out_dir, exist_ok=True)

    # list all image names and paths
    image_names = sorted([fname for fname in os.listdir(image_in_dir)])
    image_paths = sorted(
        [os.path.join(image_in_dir, fname) for fname in os.listdir(image_in_dir)]
    )

    # use the dali-based image resizing pipeline defined above
    pipeline = image_resizing_pipeline(
        file_names=image_paths, height_out=cfg.resize_height, 
        width_out=cfg.resize_width, device=cfg.device, batch_size=cfg.batch_size, 
        num_threads=10, device_id=0)
    pipeline.build()

    # the images are resized in batches
    num_batches = (
        len(image_names) // cfg.batch_size + 1
        if len(image_names) % cfg.batch_size != 0
        else 0
    )

    # loop through all the images, and resize
    cur = 0
    for _ in tqdm(range(num_batches)):
        images = pipeline.run()
        if isinstance(images[0], dali.backend_impl.TensorListGPU):
            images = images[0].as_cpu()
        images = images.as_array()
        for j in range(len(images)):
            cv2.imwrite(
                os.path.join(image_out_dir, image_names[cur]),
                cv2.cvtColor(images[j], cv2.COLOR_BGR2RGB),
            )
            cur += 1
            if cur == len(image_names):
                break  # handling last batch of a smaller size

    print(f"\n\n[TuunV2] => Image Resize Complete! Saved To: {image_out_dir}!")


    # resize the image masks and write to disk 
    csv_out_dir = resize_masks(cfg)
    print(f"\n\n[TuunV2] => CSV Seg Resize Complete! Saved To: {csv_out_dir}!\n\n")

    # also check python time for the function before returning
    time_end = time.time()
    return time.strftime("%Hh%Mm%Ss", time.gmtime(time_end - time_start))


