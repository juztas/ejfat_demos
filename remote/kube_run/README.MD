# Intro

This is a very minimal Kubernetes yamls to launch client/sender/receiver. Kubernetes networks tested:

1. hostNetwork: true
2. Multus with macvlan and pass through public IPv6/4 address inside the container.

Currently all yamls sleep infinity, but that can be modified based on experiment and pass env variables to launch senders/receivers dynamically.

## Build container

```bash
cd ejfat_demos/remote/build/
./build.sh
# It will build ejfatdemo container on your local system.
# Tag it and upload to your remote registry
```

## How to run it

1. Once updated yaml files based on your Kubernetes cluster capabilities and update image repo, launch client:

```bash
kubectl apply -f ejfatclient.yaml
```

2. Get inside the container, and reserve a Load Balancer (this requires credentials to login to LB). This will output `export EJFAT_URI=...`

```bash
export IP_VERSION=-6 # Default is IPV4. Override to 6 if needed
export EJFAT_URI_BETA="ejfats://my-super-duper-token@ejfat-lb.es.net:18008/"
ejfat reserve
cat INSTANCE_URI
```

3. Launch sender and receiver (Currently both of them sleep infinity, so order does not matter):

```bash
kubectl apply -f ejfatsender.yaml
kubectl apply -f ejfatreceiver.yaml
```

4. Inside the receiver container, execute the following commands:

```bash
export EJFAT_URI=.... # Export line received from item 2
export IP_VERSION=-6
ejfat receive
```

5. Inside the sender container, execute the following commands:

```bash
export EJFAT_URI=.... # Export line received from item 2
export IP_VERSION=-6
ejfat send
```

6. And here you are done. Test is ongoing.
