# Used dokai base as a template: https://github.com/osai-ai/dokai/blob/master/docker/Dockerfile.base

# See latest cuda tags here: https://hub.docker.com/r/nvidia/cuda/tags
FROM nvidia/cuda:11.4.0-devel-ubuntu18.04

ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND noninteractive
ENV NVIDIA_DRIVER_CAPABILITIES video,compute,utility
ENV PYTHONPATH $PYTHONPATH:/workdir
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

# Install CMake
RUN CMAKE_VERSION=3.22.2 && \
    wget https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION}/cmake-${CMAKE_VERSION}.tar.gz && \
    tar -zxvf cmake-${CMAKE_VERSION}.tar.gz && \
    cd cmake-${CMAKE_VERSION} && \
    ./bootstrap && \
    make && make install && \
    cd .. && rm -rf cmake-${CMAKE_VERSION} cmake-${CMAKE_VERSION}.tar.gz

# Install pip and setuptools
RUN pip3 install --upgrade --no-cache-dir \
    pip \
    setuptools \
    packaging 
 
# Install python packages
RUN pip3 install --no-cache-dir \
    numpy \
    opencv-python \
    scipy \
    matplotlib \
    pandas \
    scikit-learn \
    scikit-image \
    Pillow \
    librosa \
    albumentations \
    pyzmq \
    Cython \
    numba \
    requests \
    psutil \
    pydantic \
    PyYAML \
    notebook \
    ipywidgets \
    tqdm \
    pytest \
    pytest-cov \
    mypy \
    pre-commit \
    flake8 

# Copy code for cv pipeline into currently working directory
COPY . ./cv-pipeline-example
WORKDIR ./cv-pipeline-example

# Install remaining python packages
RUN pip install -r requirements.txt

# Install nvidia dali
RUN pip install --extra-index-url https://developer.download.nvidia.com/compute/redist --upgrade nvidia-dali-cuda110
