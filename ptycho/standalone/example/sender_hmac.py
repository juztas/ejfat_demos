#!/usr/bin/env python3

import os

import sys
import time

import asyncio

import hashlib
import hmac
import zlib
import requests
from urllib.parse import urlparse

sys.path.append("/src/E2SAR/build/src/pybind")
sys.path.append("/e2sar-install/lib/python3/dist-packages/")

import e2sar_py

dataset_url = os.getenv("DATAURL", "https://downloads.es.net/pub/ejfat_demos/ptycho/NS_231012080_ccdframes_0_0.stxm")

CHUNK_BYTES=8192*1000
DATA_ID = 0x0506   # decimal value: 1085
EVENTSRC_ID = 0x11223345   # decimal value: 287454020
DP_ADDR = os.environ.get("DP_ADDR", "127.0.0.1")
DP_PORT = os.environ.get("DP_PORT", 19522)
SEG_URI = f"ejfat://useless@127.0.0.1:9876/lb/1?sync=127.0.0.1:12345&data={DP_ADDR}:{DP_PORT}"
USECP = False

SEG_URI = os.environ.get("SEG_URI", SEG_URI)
HMAC_BYTES = os.environ.get("HMAC", SEG_URI).encode("utf-8")
E2SARCONFIG = os.environ.get("E2SARCONFIG", None)
# Just raise warning if file not found
if E2SARCONFIG is not None and os.path.exists(E2SARCONFIG) is False:
    print(f"Warning: E2SAR configuration file {E2SARCONFIG} not found.")
    print("Continuing with default E2SAR configuration overwrite by script")


if "useless" not in SEG_URI:
    USECP = True


def register_sender(seg_uri):
    """Register to LB"""
    if not USECP:
        print("Not using Control Plane, skipping sender registration.")
        return
    instance_uri = e2sar_py.EjfatURI(uri=seg_uri, tt=e2sar_py.EjfatURI.TokenType.instance)
    lbm = e2sar_py.ControlPlane.LBManager(instance_uri, validate_server=False)
    lbmout = lbm.add_senders([DP_ADDR])
    print(f"Registered sender to LB at {seg_uri}")
    if lbmout.has_error():
        print(f"Error registering sender to LB: {lbmout.error()}")
        raise Exception("Register sender failed")

def deregister_sender(seg_uri):
    if not USECP:
        print("Not using Control Plane, skipping deregistration.")
        return
    instance_uri = e2sar_py.EjfatURI(uri=seg_uri, tt=e2sar_py.EjfatURI.TokenType.instance)
    lbm = e2sar_py.ControlPlane.LBManager(instance_uri, validate_server=False)
    lbmout = lbm.remove_senders([DP_ADDR])
    if lbmout.has_error():
        print(f"Error deregistering sender from LB: {lbmout.error()}")
        raise Exception("Deregister sender failed")

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

def send_signed_zipped_pickle(data: bytes, sig: bytes) -> bytes:
    """Compress and sign raw bytes for transport."""
    compressed = zlib.compress(data, level=1)
    signature = hmac.new(sig, compressed, hashlib.sha256).digest()
    return signature + compressed

def configure_ejfat(segmentation_uri):
    global USECP, EVENTSRC_ID, DATA_ID

    seg_uri = e2sar_py.EjfatURI(uri=segmentation_uri, tt=e2sar_py.EjfatURI.TokenType.instance)

    if E2SARCONFIG and os.path.exists(E2SARCONFIG):
        print(f"Loading E2SAR configuration from file: {E2SARCONFIG}")
        seg = e2sar_py.DataPlane.Segmenter
        sflags = seg.SegmenterFlags
        res = sflags.getFromINI(E2SARCONFIG)
        sflags = res.value()
    else:
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
    if res.lastErrno != 0:
        print(f"Error encountered after opening send socket: {res[2]}")
        # exit(-1)

    return seg


async def recv_and_process():
    global dataset_url

    seg = configure_ejfat(SEG_URI)

    try:
        parsed = urlparse(dataset_url)
        scheme = parsed.scheme.lower()

        if scheme in ("http", "https"):
            # Remote dataset via HTTP(S)
            response = requests.get(dataset_url, stream=True)
            response.raise_for_status()
            data_stream = response.iter_content(chunk_size=CHUNK_BYTES)
            print("Starting HTTP download")
        elif scheme == "file":
            # Local dataset file
            local_path = parsed.path
            if not os.path.exists(local_path):
                raise FileNotFoundError(f"Local file not found: {local_path}")
            data_stream = _read_file_chunks(local_path, CHUNK_BYTES)
            print(f"Reading local file: {local_path}")
        else:
            raise ValueError(f"Unsupported URL scheme: {scheme}")

        total_sent = 0
        for chunk in data_stream:
            if not chunk:
                continue

            total_sent += len(chunk)
            print(f"Total chunk sent: {total_sent}")

            msg_pickle = send_signed_zipped_pickle(chunk, HMAC_BYTES)
            res = seg.sendEvent(msg_pickle, len(msg_pickle), int(time.time() * 1e6))
            assert res.value() == 0

            stats = seg.getSendStats()
            if stats.lastErrno != 0:
                print(f"  SendStats: {stats}")
                print("  Error encountered sending event frame")

        # Send termination message
        final_message = send_signed_zipped_pickle(b"__END__", HMAC_BYTES)
        res = seg.sendEvent(final_message, len(final_message), int(time.time() * 1e6))
        print("File transmitted successfully")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def _read_file_chunks(path, chunk_size):
    """Generator to read local file in chunks."""
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk


async def main():
    try:
        register_sender(SEG_URI)
        print("Sender registered.")
        await asyncio.sleep(1)  # Give some time for registration to complete
    except Exception as e:
        print(f"Error registering sender: {e}")
        return
    await asyncio.gather(recv_and_process())
    try:
        deregister_sender(SEG_URI)
        print("Sender deregistered.")
    except Exception as e:
        print(f"Error deregistering sender: {e}")

if __name__ == "__main__":
    asyncio.run(main())