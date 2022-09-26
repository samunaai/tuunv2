# Lifted from Dokai base image at https://github.com/osai-ai/dokai/blob/61cf10567cced9b8a5af2855ec880e8730532916/docker/Dockerfile.base
# some things may not be needed, made a few changes as well
# See latest cuda tags here: https://hub.docker.com/r/nvidia/cuda/tags
FROM nvidia/cuda:11.4.0-devel-ubuntu18.04

ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND noninteractive
ENV NVIDIA_DRIVER_CAPABILITIES video,compute,utility
ENV PYTHONPATH $PYTHONPATH:/workdir

COPY . ./workdir

WORKDIR /workdir

# Install python and apt-get packages
 RUN apt-get update && apt -y upgrade && \
     apt-get -y install \
     software-properties-common \
     build-essential yasm nasm ninja-build \
    unzip git wget curl nano vim tmux \
    sysstat libtcmalloc-minimal4 pkgconf \
    autoconf libtool flex bison \
    libsm6 libxext6 libxrender1 libgl1-mesa-glx \
    libx264-dev libsndfile1 libmp3lame-dev libssl-dev \
    python3 python3-dev python3-pip libpng-dev libjpeg-dev \
    liblapack-dev libopenblas-dev gfortran && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    apt-get clean && \
    apt-get -y autoremove && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/apt/archives/*


# Install pip and setuptools
RUN pip3 install --upgrade --no-cache-dir \
    pip \
    setuptools \
    packaging
 
                 
# Install python packages
RUN pip3 install --no-cache-dir \
    numpy \
    scikit-learn \
    scikit-image \
    botorch
