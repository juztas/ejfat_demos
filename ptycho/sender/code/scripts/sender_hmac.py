#!/usr/bin/env python3

import os
import zmq
import zmq.asyncio

import sys
import time

import copy

import asyncio

import math
import struct
import datetime

import hashlib
import hmac
import pickle
import zlib


sys.path.append("/src/E2SAR/build/src/pybind")
sys.path.append("/e2sar-install/lib/python3/dist-packages/")

import e2sar_py

ccd_sub_address = os.environ.get("ZMQ_SUB_ADDRESS")

DATA_ID = 0x0506   # decimal value: 1085
EVENTSRC_ID = 0x11223345   # decimal value: 287454020

SEG_URI = os.environ["SEG_URI"]
HMAC_BYTES = os.environ.get("HMAC", SEG_URI).encode("utf-8")

####################
####################
####################
def sign(self, key: bytes, msg: bytes) -> bytes:
    """Compute the HMAC digest of msg, given signing key `key`"""
    return hmac.HMAC(
        key,
        msg,
        digestmod=hashlib.sha256,
    ).digest()

def send_signed_zipped_pickle(obj, key):
    """pickle an object, zip and sign the pickled bytes before sending"""
    zobj = zlib.compress(obj)
    signature = sign(key, zobj)

    # signature is 32 + z
    return signature + z

def configure_ejfat(segmentation_uri):
    seg_uri = e2sar_py.EjfatURI(uri=segmentation_uri, tt=e2sar_py.EjfatURI.TokenType.instance)

    sflags = e2sar_py.DataPlane.Segmenter.SegmenterFlags()
    # sflags.useCP = False  # turn off CP. Default value is True
    sflags.syncPeriodMs = 1000
    sflags.syncPeriods = 5

    assert(sflags.syncPeriodMs == 1000)
    assert(sflags.useCP == True)
    assert(sflags.syncPeriods == 5)

    print("Segmenter flags:")
    print(f"  syncPeriodMs={sflags.syncPeriodMs}")
    print(f"  useCP={sflags.useCP}")
    print(f"  mtu={sflags.mtu}")
    print(f"  syncPeriods={sflags.syncPeriods}")

    seg = e2sar_py.DataPlane.Segmenter(seg_uri, DATA_ID, EVENTSRC_ID, sflags)

    send_context = "".encode('utf-8')

    # Start segmenter threads
    res = seg.OpenAndStart()
    assert res.value() == 0

    res = seg.getSendStats()
    if (res.lastErrno != 0):
        print(f"Error encountered after opening send socket: {res[2]}")
        # exit(-1)

    return seg

ctx = zmq.asyncio.Context()

async def recv_and_process(queue):
    sock = ctx.socket(zmq.SUB)
    sock.setsockopt(zmq.SUBSCRIBE, b"")
    sock.connect(ccd_sub_address)

    while True:
        try:
            msg = await sock.recv_multipart()  # waits for msg to be ready
            await queue.put(msg)
        except Exception as e:
            print(repr(e))

async def transmit(queue):
    global ccd_pub_address, DATA_ID, EVENTSRC_ID, SEG_URI

    seg = configure_ejfat(SEG_URI)

    while True:
        try:
            msg = await queue.get()
            msg_pickle = copy.copy(msg)
            msg_pickle = msg_pickle[0]
            msg_pickle = send_signed_zipped_pickle(msg_pickle, HMAC_BYTES)

            res = seg.sendEvent(msg_pickle, len(msg_pickle), int(time.time()*1e6))

            assert(res.value() == 0)

            res = seg.getSendStats()
            if (res.lastErrno != 0):
                print(f"  SendStats: {res}")
                print(f"  Error encountered sending event frame")

        except Exception as e:
            print(repr(e))

async def main():
    queue = asyncio.Queue()
    await asyncio.gather(recv_and_process(queue), transmit(queue))

if __name__ == "__main__":
    asyncio.run(main())

