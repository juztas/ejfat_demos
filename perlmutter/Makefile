#
#  This makefile runs on a Perlmutter login node, and provides the podman-hpc and slurm commands
#  to build and operate the EJFAT load balancer.
#
#  Yatish Kumar
#  July 2024
#------------------------------------------------------------------------------------------------

.PHONY: help build reserve free receive send monitor send_file receive_file

IP_VERSION ?= "-6"

ifeq ($(IP_VERSION),"-4")
  LB_IP ?= $(shell dig +short ejfat-lb.es.net A | tail -1 )
  MY_IP ?= $(shell ip route get $(LB_IP) | head -1 | sed 's/^.*src//' | awk '{ print $$1 }')
else
  LB_IP ?= $(shell dig +short ejfat-lb.es.net AAAA | tail -1 )
  MY_IP ?= $(shell ip route get $(LB_IP) | head -1 | sed 's/^.*src//' | awk '{ print $$1 }')
endif

INSTANCE_URI := $(shell cat INSTANCE_URI | sed 's/^[^=]*=//' - )
LB_IP ?= $(shell dig +short ejfat-lb.es.net AAAA | tail -1 )
MY_IP ?= $(shell ip route get $(LB_IP) | head -1 | sed 's/^.*src//' | awk '{ print $$1 }')

RX_DURATION ?= 120
RX_THREADS ?= 16
TX_RATE     ?= 0.1
SEND_SOCKETS ?= 8
NFRAMES = 20000
DATA_ID ?= $(shell bash -c 'echo $$(( $$RANDOM % 1000 + 1 ))')

test :
	@echo $(MY_IP)
	@echo "SCRATCH IS $(SCRATCH)"

help : 
	podman-hpc run \
		-v ./:/ejfat_demos/perlmutter \
		--network host --rm -it --entrypoint= \
		e2sar_dev /ejfat_demos/perlmutter/help
	@echo " Good Luck "

build :  
	cd .. ; podman-hpc build -t e2sar_dev:latest -f Containerfile.perlmutter
	podman-hpc migrate e2sar_dev:latest

reserve :
	podman-hpc run --cap-add=NET_RAW --cap-add=NET_ADMIN \
		-v ./:/ejfat_demos/perlmutter \
		--env EJFAT_URI_BETA=$(EJFAT_URI_BETA) \
		--env IP_VERSION=$(IP_VERSION) \
		--network host --rm -it --entrypoint= \
		e2sar_dev /ejfat_demos/perlmutter/reserve | grep "EJFAT_URI" >  ./INSTANCE_URI

receive :
	podman-hpc run \
		-v ./:/ejfat_demos/perlmutter \
		--env EJFAT_URI=$(INSTANCE_URI) \
		--env IP_VERSION=$(IP_VERSION) \
		--env MY_IP=$(MY_IP) \
		--env RX_DURATION=$(RX_DURATION) \
		--env RX_THREADS=$(RX_THREADS)  \
		--network host --rm -it --entrypoint= \
		e2sar_dev /ejfat_demos/perlmutter/receive

send :
	podman-hpc run \
		-v ./:/ejfat_demos/perlmutter \
		--env EJFAT_URI=$(INSTANCE_URI) \
		--env IP_VERSION=$(IP_VERSION) \
		--env MY_IP=$(MY_IP) \
		--env SEND_SOCKETS=$(SEND_SOCKETS) \
		--env NFRAMES=$(NFRAMES) \
		--env TX_RATE=$(TX_RATE) \
		--env DATA_ID=$(DATA_ID) \
		--network host --rm -it --entrypoint= \
		e2sar_dev /ejfat_demos/perlmutter/send

gen_test_files :
	podman-hpc run \
		-v ./:/ejfat_demos/perlmutter \
		--rm --network host -v $(SCRATCH)/storage/ejfat_ft/data:/data \
		e2sar_dev generate-random-files.sh -s 300 -p test -e root -d /data -n 25

receive_file :
	-rm -r $(SCRATCH)/storage/ejfat_ft/data_rx
	mkdir -p $(SCRATCH)/storage/ejfat_ft/data_rx
	podman-hpc run \
		-v ./:/ejfat_demos/perlmutter \
		--env EJFAT_URI=$(INSTANCE_URI) \
		--env IP_VERSION=$(IP_VERSION) \
		-v $(SCRATCH)/storage/ejfat_ft/data_rx:/data \
		--network host --rm -it  --entrypoint= \
		e2sar_dev /ejfat_demos/perlmutter/receive_file

send_file :
	podman-hpc run \
		-v ./:/ejfat_demos/perlmutter \
		--env EJFAT_URI=$(INSTANCE_URI) \
		--env IP_VERSION=$(IP_VERSION) \
		--env NFRAMES=10000 \
		--env SEND_SOCKETS=$(SEND_SOCKETS) \
		-v $(SCRATCH)/storage/ejfat_ft/data:/data \
		--network host --rm -it --entrypoint= \
		e2sar_dev /ejfat_demos/perlmutter/send_file


monitor :
	podman-hpc run \
		-v ./:/ejfat_demos/perlmutter \
		--env EJFAT_URI=$(INSTANCE_URI) \
		--env IP_VERSION=$(IP_VERSION) \
		--network host --rm -it --entrypoint= \
		e2sar_dev /ejfat_demos/perlmutter/monitor

free :
	podman-hpc run \
		-v ./:/ejfat_demos/perlmutter \
		--env EJFAT_URI=$(INSTANCE_URI) \
		--env IP_VERSION=$(IP_VERSION) \
		--network host --rm -it --entrypoint= \
		e2sar_dev /ejfat_demos/perlmutter/free
