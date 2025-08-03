Instructions
============

* Requires: Nvidia-GPU enabled device
* Build container: ```docker build -t ptycho_ejfat_demo .```
* Make output directory: mkdir data # to store streamed results

Standalone Mode
===============
* Run the script directly: ```docker run --user $(id -u):$(id -g) --net=host --gpus=all -v "$PWD/example:/example" -v "$PWD/data:/data" --rm -it ptycho_ejfat_demo python3 /example/main.py```

EJFAT Mode
===========

* Start receiver EJFAT: ```docker run --user $(id -u):$(id -g) --net=host --gpus=all -v "$PWD/example:/example" -v "$PWD/data:/data" --rm -it ptycho_ejfat_demo python3 /example/recv_hmac.py```
* Trigger sender EJFAT: ```docker run --user $(id -u):$(id -g) --net=host --gpus=all -v "$PWD/example:/example" -v "$PWD/data:/data" --rm -it ptycho_ejfat_demo python3 /example/sender_hmac.py```
