FROM ghcr.io/osai-ai/dokai:22.03-base
COPY . ./cv-pipeline-example
WORKDIR ./cv-pipeline-example
RUN pip install -r requirements.txt
RUN pip install --extra-index-url https://developer.download.nvidia.com/compute/redist --upgrade nvidia-dali-cuda110
