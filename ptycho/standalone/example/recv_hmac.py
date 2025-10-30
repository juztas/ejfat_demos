#!/usr/bin/env python3

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

from preprocess import *
from reconstruct import *
from display import *

from process_stxm_file import process_file_std

verbose = True

# Example paths
basedir = os.getenv("WORKDIR", "/data")
dataset_path = os.getenv("DATAPATH", os.path.join(basedir, "streamed_dataset.stxm"))
savefile_path = os.getenv("SAVEPATH", dataset_path.replace(".stxm", "") + ".mat")
cxi_path = os.getenv("CXIPATH", dataset_path.replace(".stxm", "") + ".cxi")
n_iterations = int(os.getenv("N_ITERATIONS", "20"))

if os.getenv("PRECREATE_DIRS", "0") == "1":
    os.makedirs(os.path.dirname(dataset_path), exist_ok=True)
    os.makedirs(os.path.dirname(savefile_path), exist_ok=True)
    os.makedirs(os.path.dirname(cxi_path), exist_ok=True)

DP_IPV4_ADDR = os.environ.get("DP_ADDR", "127.0.0.1")
DP_IPV4_PORT = os.environ.get("DP_PORT", 19522)
REAS_URI = f"ejfat://useless@127.0.0.1:9876/lb/1?sync=127.0.0.1:12345&data={DP_IPV4_ADDR}:{DP_IPV4_PORT}"

DATA_ID = 0x0506   # decimal value: 1085
# Set the reassembler URI
REAS_URI_ = os.environ.get("REAS_URI", REAS_URI)
HMAC_BYTES = os.environ.get("HMAC", REAS_URI_).encode("utf-8")

reas_uri = e2sar_py.EjfatURI(uri=REAS_URI_, tt=e2sar_py.EjfatURI.TokenType.instance)

USECP = False

if "useless" not in REAS_URI:
    USECP = True

def sign(key: bytes, msg: bytes) -> bytes:
    """Compute the HMAC digest of msg, given signing key `key`"""
    return hmac.HMAC(
        key,
        msg,
        digestmod=hashlib.sha256,
    ).digest()

def recv_signed_zipped_pickle(obj, sig):
    """inverse of send_signed_zipped_pickle. The digest for hashlib.sha256 = 32 bytes"""
    rsignature = obj[0:32]
    obj = obj[32:]

    # check signature before deserializing
    correct_signature = sign(sig, obj)
    if not hmac.compare_digest(rsignature, correct_signature):
        raise ValueError("invalid signature")
    p = zlib.decompress(obj)
    return p

def print_stats(stats):
    print(f' stats: enqueueLoss    {stats.enqueueLoss}')
    print(f'        reassemblyLoss {stats.reassemblyLoss}')
    print(f'        eventSuccess   {stats.eventSuccess}')
    print(f'        grpcErrCnt     {stats.grpcErrCnt}')
    print(f'        dataErrCnt     {stats.dataErrCnt}')
    print(f'        lastE2SARError {stats.lastE2SARError}')
    print(f'        lastErrno      {stats.lastErrno}')

def init_ejfat():
    global USECP
    # Get data plane IPv4 address
    print("Data Plane Address (v4):", str(reas_uri.get_data_addr_v4().value()[0]))

    # Config the reassembler flags
    rflags = e2sar_py.DataPlane.Reassembler.ReassemblerFlags()

    # These two flags are needed to make direct connection without LB work
    if not USECP:
        rflags.useCP = False  # turn off CP. Default value is True
        rflags.withLBHeader = True  # LB header will be attached since there is no LB
    else:
        rflags.useCP = True  # turn off CP. Default value is True
        rflags.withLBHeader = False  # LB header will be attached since there is no LB


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

    assert res.value() == 0
    print("Worker reg: ", res)

    res = reas.OpenAndStart()  # the DP address must be available
    assert res.value() == 0
    print_stats(reas.getStats())

    return reas

def read_and_process(dataset_path):
    global verbose

    reas = init_ejfat()
    
    dataset = open(dataset_path, "wb")

    # Get file
    while True:
        try:
            recv_event_len, recv_bytes, recv_event_num, recv_data_id = reas.recvEventBytes(wait_ms=1000)
            if (recv_event_len <= 0):  # -1 or -2 (has_error)
                print(f'Error or Timeout: {recv_event_len}')
                print_stats(reas.getStats())
                continue

            if verbose:
                print(f'Rx Event: #{recv_event_num} from Data ID {recv_data_id} with length {recv_event_len}')
                print_stats(reas.getStats())
            recv_bytes = recv_signed_zipped_pickle(recv_bytes, HMAC_BYTES)

            if recv_bytes:
                if len(recv_bytes) < 10 and recv_bytes == b"__END__":
                    print("Closing file", dataset_path)
                    dataset.close()
                    break
                        
                dataset.write(recv_bytes)
        except Exception as e:
            print("Exception occurred", repr(e))

if __name__ == "__main__":
    args = {
        "path": cxi_path,
        "n_energies": 1,
        "n_regions": 1,
        "energy_start_index": 0,
        "region_start_index": 0,
        "n_modes": 3,
        "n_iter": n_iterations,
        "probe_support_radius": 150,
        "translation_randomization": False,
        "simulate_probe_translation": False,
        "propagation_distance": 25e-6,
        "probefile": None,
        "basedir": basedir,
        "fourier_mask": True,
        "refine_positions": True,
        "refine_probe": True,
        "refine_background": True,
        "verbose": True,
        "preprocess": False,
        "start_frames_to_ignore": 10,
        "save": True,
        "savefile": savefile_path}

    # additional args
    args["monitor"] = False
    args["oversampling_factor"] = 1

    # some defaults
    n_energies = args["n_energies"]
    energy_start_index = args["energy_start_index"]

    # read and process incoming stream file
    read_and_process(dataset_path)

    # convert raw file into a CXI file
    process_file_std(dataset_path, cxi_path)

    # Process the CXI 
    args_list = [args.copy()]
    if args["preprocess"]:
        print("[ACME] Analyzing file: %s" %args_list[0]["path"])

        results = []
        for args in args_list:
            result = preprocess(args_list)
            results.append(result)

    results = []

    for args in args_list:
        result = reconstruct_from_cxi(args)
        results.append(result)

    #Show results
    show_results(loadmat(savefile_path), basedir, n=440)

