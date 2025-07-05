#
#  This makefile runs on a Perlmutter login node, and provides the podman-hpc and slurm commands
#  to build and operate the EJFAT load balancer.
#
#  Yatish Kumar
#  July 2024
#------------------------------------------------------------------------------------------------

.PHONY: help build reserve free receive send monitor

INSTANCE_URI := $(shell cat INSTANCE_URI | sed 's/^[^=]*=//' - )

help : 
	podman-hpc run --env EJFAT_URI_BETA=$(EJFAT_URI_BETA) --network host --rm -it --entrypoint= e2sar_dev /ejfat_demos/perlmutter/help
	@echo " Good Luck "

build :  
	cd .. ; podman-hpc build -t e2sar_dev:latest -f Containerfile.perlmutter
	podman-hpc migrate e2sar_dev:latest

reserve :
	podman-hpc run --env EJFAT_URI_BETA=$(EJFAT_URI_BETA) --network host --rm -it --entrypoint= e2sar_dev /ejfat_demos/perlmutter/reserve | grep "EJFAT_URI" >  ./INSTANCE_URI

receive :
	podman-hpc run --env EJFAT_URI=$(INSTANCE_URI) --env RX_DURATION=0 --network host --rm -it --entrypoint= e2sar_dev /ejfat_demos/perlmutter/receive

send :
	podman-hpc run --env EJFAT_URI=$(INSTANCE_URI) --env RX_DURATION=0 --network host --rm -it --entrypoint= e2sar_dev /ejfat_demos/perlmutter/send

monitor :
	podman-hpc run --env EJFAT_URI=$(INSTANCE_URI) --env RX_DURATION=0 --network host --rm -it --entrypoint= e2sar_dev /ejfat_demos/perlmutter/monitor

free :
	echo $$EJFAT_URI
	podman-hpc run --env EJFAT_URI=$(INSTANCE_URI) --network host --rm -it --entrypoint= e2sar_dev /ejfat_demos/perlmutter/free
