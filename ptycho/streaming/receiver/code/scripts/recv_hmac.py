#!/usr/bin/env python3

import zmq
import pickle
import os
import sys

sys.path.append("/e2sar-install/lib/python3/dist-packages/")

import e2sar_py
import uuid
import time, struct, datetime

import hashlib
import hmac
import pickle
import zlib


DP_IPV4_ADDR = os.environ.get("DP_ADDR")
DP_IPV4_PORT = os.environ.get("DP_PORT")
DP_PUB_ADDRESS = os.environ.get("DP_PUB_ADDRESS") 

context = zmq.Context()
sock = context.socket(zmq.PUB)

sock.bind(DB_PUB_ADDRESS)

DATA_ID = 0x0506   # decimal value: 1085

# Set the reassembler URI
REAS_URI_ = os.environ["SEG_URI"]
HMAC_BYTES = os.environ.get("HMAC", REAS_URI_).encode("utf-8")

reas_uri = e2sar_py.EjfatURI(uri=REAS_URI_, tt=e2sar_py.EjfatURI.TokenType.instance)

def sign(key: bytes, msg: bytes) -> bytes:
    """Compute the HMAC digest of msg, given signing key `key`"""
    return hmac.HMAC(
        key,
        msg,
        digestmod=hashlib.sha256,
    ).digest()

def recv_signed_zipped_pickle(obj, sig):
    """inverse of send_signed_zipped_pickle"""
    rhmac = obj[0:32]
    obj = obj[32:]

    # check signature before deserializing
    correct_signature = sign(sig, obj)
    if not hmac.compare_digest(rhmac, correct_signature):
        raise ValueError("invalid signature")
    p = zlib.decompress(obj)
    return pickle.loads(p)

# Make sure the token matches the one in the string
def get_inst_token(uri : e2sar_py.EjfatURI):
    try:
        token = uri.get_instance_token().value()
        print("Instance Token:", token)
    except RuntimeError as e:
        print("Instance Token - Error:", e)

get_inst_token(reas_uri)

# Get data plane IPv4 address
print("Data Plane Address (v4):", str(reas_uri.get_data_addr_v4().value()[0]))

# Config the reassembler flags

rflags = e2sar_py.DataPlane.Reassembler.ReassemblerFlags()
#rflags.useCP = False  # turn off CP. Default value is True
#rflags.withLBHeader = True  # LB header will be attached since there is no LB

#assert rflags.period_ms == 100  # default value of the C++ constructor
#assert rflags.useCP == False

print("Reassembler flags:")
print(f"  period_ms={rflags.period_ms}")  # should be 100 according to the C++ constructor
print(f"  useCP={rflags.useCP}")
print(f"  validateCert = {rflags.validateCert}")
print(f"  epoch_ms = {rflags.epoch_ms}")
print(f"  setPoint = {rflags.setPoint}")
print(f"  [Kp, Ki, Kd] = [{rflags.Kp}, {rflags.Ki}, {rflags.Kd}]")
print(f"  [weight, min_factor, max_factor] = [{rflags.weight}, {rflags.min_factor}, {rflags.max_factor}]")
print(f"  portRange = {rflags.portRange}")
print(f"  withLBHeader = {rflags.withLBHeader}")


print(e2sar_py.IPAddress.from_string(DP_IPV4_ADDR))

# Init the reassembler object
reas = e2sar_py.DataPlane.Reassembler(
    reas_uri, e2sar_py.IPAddress.from_string(DP_IPV4_ADDR), DP_IPV4_PORT, 1, rflags)

res = reas.registerWorker(str(uuid.uuid4())) ####
#res = reas.registerWorker("ptycho-worker") ####
#TODO: check on value
assert res.value() == 0
print("Worker reg", res)

res = reas.OpenAndStart()  # the DP address must be available

assert res.value() == 0

def print_stats(stats):
    print(f' stats: enqueueLoss    {stats.enqueueLoss}')
    print(f'        reassemblyLoss {stats.reassemblyLoss}')
    print(f'        eventSuccess   {stats.eventSuccess}')
    print(f'        grpcErrCnt     {stats.grpcErrCnt}')
    print(f'        dataErrCnt     {stats.dataErrCnt}')
    print(f'        lastE2SARError {stats.lastE2SARError}')
    print(f'        lastErrno      {stats.lastErrno}')

print_stats(reas.getStats())

while True:
    try:
        recv_event_len, recv_bytes, recv_event_num, recv_data_id = reas.recvEventBytes(wait_ms=1000)
        if (recv_event_len <= 0):  # -1 or -2 (has_error)
            print(f'Error or Timeout: {recv_event_len}')
            print_stats(reas.getStats())
            continue

        print(f'Rx Event: #{recv_event_num} from Data ID {recv_data_id} with length {recv_event_len}')
        print_stats(reas.getStats())
        recv_bytes = recv_signed_zipped_pickle(recv_bytes, HMAC_BYTES)

        if recv_bytes:
            sock.send(recv_bytes)
    except Exception as e:
        print("Exception occurred", repr(e))

