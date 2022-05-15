# Cloud Segmentation Pipeline

## Summary

The following codebase illustrates an example of Computer Vision pipeline for image segmentation. It consists of three different stages:
- Preprocessing
- Training
- Postprocessing

## Preprocessing

Machine Learning models receive data as an input. It is important to ensure that the data is supplied in the right format. For example, one specific case of data preprocessing is data transformation. In the context of images it might include applying an image enhancement technique such as denoising and debluring. Moreover, one can also change the format of the data. For example, it might be faster to read numpy arrays in the memory than images in png format. In our case, we transform the images by resizing them to a different resolution. It will allow us to save additional time during the training stage, by eliminating the need to calling resize transform every time the data loader will load the image from the model, becaus the image will be already resized to the right resolution beforehand.

On this stage we have the following hyperparameters: 
- resize output width
- resize output height
- backend for the resizing algorithm: cpu or gpu
- batch size when loading images for the resizing operator


## Training

Training stage includes training a machine learning model on some specific set of data. In our case we will be training an image segementation model which follows the encoder-decoder architecture paradigm. 

On this stage we have the following hyper parameters: 
- learning rate of the encoder
- learning rate of the decoder
- number of training epochs
- optimizer (Adam, etc)
- encoder model (resnet18, resnet50, etc)

## Postrprocessing

Postprocessing commonly refers to the set of methods that apply some transformation to the final prediction of the model. In our case the model predicts raw segmentation masks - a matrix which contains the real values between 0 and 1. To obtain a binary mask we need to apply tresholding operation to a segmentation mask with raw values. Furthermore, after generating a binary mask we want to eliminate masks of the small size using another threshold. Removal of small masks is driven by the idea that humans who were annotating the original training dataset wouldn't typically produce mask of a a very small size as it is time very consuming and would rather group several adjacent cloud regions into one region of a bigger size.

On this stage we have the following hyper parameters: 
- threshold for converting from raw segmentation masks to binary segmentation masks
- minimal mask size: pixel size of the minimum region to be left as a cloud
