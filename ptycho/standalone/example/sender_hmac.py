#!/usr/bin/env python3

import os

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
import requests

sys.path.append("/src/E2SAR/build/src/pybind")
sys.path.append("/e2sar-install/lib/python3/dist-packages/")

import e2sar_py

dataset_url = os.getenv("DATAURL", "https://downloads.es.net/pub/ejfat_demos/ptycho/NS_231012080_ccdframes_0_0.stxm")

CHUNK_BYTES=8192*1000
DATA_ID = 0x0506   # decimal value: 1085
EVENTSRC_ID = 0x11223345   # decimal value: 287454020
DP_IPV4_ADDR = os.environ.get("DP_ADDR", "127.0.0.1")
DP_IPV4_PORT = os.environ.get("DP_PORT", 19522)
SEG_URI = f"ejfat://useless@127.0.0.1:9876/lb/1?sync=127.0.0.1:12345&data={DP_IPV4_ADDR}:{DP_IPV4_PORT}"
USECP = False

SEG_URI = os.environ.get("SEG_URI", SEG_URI)
HMAC_BYTES = os.environ.get("HMAC", SEG_URI).encode("utf-8")

if "useless" not in SEG_URI:
    USECP = True

####################
####################
####################
def sign(key: bytes, msg: bytes) -> bytes:
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

    # hashlib.sha256 generates at 32 byte signature therefore the stream is 32 + z (size)
    # if flexibility is needed then maybe first byte is size for size of signature
    return signature + zobj

def configure_ejfat(segmentation_uri):
    global USECP, EVENTSRC_ID, DATA_ID

    seg_uri = e2sar_py.EjfatURI(uri=segmentation_uri, tt=e2sar_py.EjfatURI.TokenType.instance)

    sflags = e2sar_py.DataPlane.Segmenter.SegmenterFlags()

    sflags.useCP = USECP  # turn off CP. Default value is True
    sflags.syncPeriodMs = 1000
    sflags.syncPeriods = 5

    print("Segmenter flags:")
    print(f"  syncPeriodMs={sflags.syncPeriodMs}")
    print(f"  useCP={sflags.useCP}")
    print(f"  mtu={sflags.mtu}")
    print(f"  syncPeriods={sflags.syncPeriods}")

    seg = e2sar_py.DataPlane.Segmenter(seg_uri, DATA_ID, EVENTSRC_ID, sflags)

    # Start segmenter threads
    res = seg.OpenAndStart()
    assert res.value() == 0

    res = seg.getSendStats()
    if (res.lastErrno != 0):
        print(f"Error encountered after opening send socket: {res[2]}")
        # exit(-1)

    return seg

async def recv_and_process():
    global dataset_url

    seg = configure_ejfat(SEG_URI)

    try:
        response = requests.get(dataset_url, stream=True) # Use stream=True for large files
        response.raise_for_status()

        # Open the local file in binary write mode
        # Iterate over the response content in chunks
        print("Starting download")

        chunk_size = 0
        for chunk in response.iter_content(chunk_size=CHUNK_BYTES):
            chunk_size = chunk_size + len(chunk)
            if chunk:  # Filter out keep-alive new chunks
                print("Total chunk sent: ", chunk_size)
                msg_pickle = send_signed_zipped_pickle(chunk, HMAC_BYTES)
                res = seg.sendEvent(msg_pickle, len(msg_pickle), int(time.time()*1e6))
                assert(res.value() == 0)

                res = seg.getSendStats()

                if (res.lastErrno != 0):
                    print(f"  SendStats: {res}")
                    print(f"  Error encountered sending event frame")

        # Send close message
        final_message = send_signed_zipped_pickle(b"__END__", HMAC_BYTES)
        res = seg.sendEvent(final_message, len(final_message), int(time.time()))
        print(f"File transmitted successfully")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

async def main():
    await asyncio.gather(recv_and_process())

if __name__ == "__main__":
    asyncio.run(main())
