IPADDR="0.0.0.0"
LBNAME="ptycho-example-$RANDOM"
CONTAINER="stac-e2sar-zmq:0.2.1a3"

# Extract EJFAR_URI from following command
#docker run --rm -it --env EJFAT_URI=${EJFAT_ADMIN_URI} --net=host stac-e2sar-zmq:0.2.1a3 lbadm --reserve --duration 0 --lbname $LBNAME -a $IPADDR

docker run --name zmq-to-ejfat --net=host -v "./sender/code/scripts:/scripts" --env SEG_URI=${EJFAT_URI} --rm -it $CONTAINER /scripts/sender.py

docker run --name ejfat-to-zmq --net=host -v "./receiver/code/scripts:/scripts" --env SEG_URI=${EJFAT_URI} --rm -it $CONTAINER /scripts/recv.py


