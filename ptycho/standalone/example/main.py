import os
import time
import requests

from preprocess import *
from reconstruct import *
from display import *

from process_stxm_file import process_file_std

basedir = os.getenv("WORKDIR", "/data")

# download the dataset
dataset_url = os.getenv("DATAURL", "https://downloads.es.net/pub/ejfat_demos/ptycho/NS_231012080_ccdframes_0_0.stxm")

dataset_path = os.getenv("DATAPATH", os.path.join(basedir, os.path.basename(dataset_url)))
savefile_path = os.getenv("SAVEPATH", dataset_path.replace(".stxm", "") + ".mat")
cxi_path = os.getenv("CXIPATH", dataset_path.replace(".stxm", "") + ".cxi")

n_iterations = os.getenv("N_ITERATIONS", 20)

def download_file(url, save_path):
    try:
        response = requests.get(url, stream=True) # Use stream=True for large files
        response.raise_for_status()

        # Open the local file in binary write mode
        with open(save_path, 'wb') as file:
            # Iterate over the response content in chunks
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # Filter out keep-alive new chunks
                    file.write(chunk)

        print(f"File downloaded successfully to: {save_path}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

print(f"Downloading file: {dataset_url} to {dataset_path}")
if not os.path.exists(dataset_path):
    download_file(dataset_url, dataset_path)

process_file_std(dataset_path, cxi_path)
print(cxi_path)

def main(args):
    # some defaults
    n_energies = args["n_energies"]
    energy_start_index = args["energy_start_index"]

    args["monitor"] = False
    args["oversampling_factor"] = 1

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

    return results

if __name__ == "__main__":
    args = {
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
        "path": cxi_path,
        "savefile": savefile_path}

    t0 = time.time()
    results1 = main(args)

    ##The results can only be shown after they are gathered, otherwise this will fail.
    show_results(loadmat(savefile_path), basedir, n=440)
