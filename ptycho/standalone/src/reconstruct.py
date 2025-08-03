###CDTOOLS reconstruction code
import cdtools
from cdtools.tools import image_processing as ip
from readCXI import *
import torch as t
import numpy as np
from scipy import io
from copy import deepcopy
import argparse
import time
#from dask.distributed import print
import h5py

def reconstruct_from_cxi(args):
    dataset = load_cxi_file(args['path'])
    print('[CDTOOLS] Analyzing CXI file: %s' %args['path'])
    if args["start_frames_to_ignore"] > 0:
        start_frame = args["start_frames_to_ignore"]
        print("[CDTOOLS] Ignoring first %i frames" %start_frame)
        dataset.translations = dataset.translations[start_frame:]
        dataset.patterns = dataset.patterns[start_frame:]

    # We move the model to the GPU
    model = make_model_from_dataset(dataset,args)
    device = 'cuda:0'
    model.to(device=device)
    dataset.get_as(device=device)
    #get the probe Fourier mask from the cxi file and move to GPU
    px = readCXI(args["path"])
    dir(px)
    model.probe.fourier_mask = t.as_tensor(readCXI(args["path"]).probemask, device = device)

    if not args["refine_positions"]:
        model.translation_offsets.requires_grad = False
    if not args["refine_background"]:
        model.background.requires_grad = False
    if not args["refine_probe"]:
        model.probe.requires_grad = False
    
    # We run the actual reconstruction
    for i, loss in enumerate(model.Adam_optimize(args['n_iter'], dataset,lr=0.005, batch_size=50,schedule=True)):
        # We print a quick report of the optimization status
        if i % 5 == 0:
            #apply Fourier mask to the probe
            if args["fourier_mask"]:
                for i in range(args['n_modes']):
                    model.probe.data[i] = t.fft.ifft2(t.fft.fft2(model.probe.data[i])*model.probe.fourier_mask)
            print('[CDTOOLS] ' + model.report())
            if args["monitor"]:
                # And liveplot the updates to the model as they happen
                model.inspect(dataset)
    model.tidy_probes()
    if args["save"]:
        save_results(args["savefile"].replace('.mat','.mat'), model, dataset)
        
    print("[CDTOOLS] Reconstruction completed.")
    return args

def load_cxi_file(path):
    return cdtools.datasets.Ptycho2DDataset.from_cxi(path)

def make_model_from_dataset(dataset, args):
    monitor = args['monitor']
    if monitor:
        dataset.inspect()
    model = cdtools.models.FancyPtycho.from_dataset(
        dataset, n_modes=args['n_modes'],
        oversampling=args['oversampling_factor'],
        propagation_distance=args['propagation_distance'],
        simulate_probe_translation=args['simulate_probe_translation'],
        probe_support_radius=args['probe_support_radius'],
        translation_scale=1,
        units='um')

    if args['probefile'] is not None:
        try:
            print("[CDTOOLS] Using file %s for the probe." % args['probefile'])
            if ".mat" in args['probefile']:
                data = io.loadmat(args['probefile'])
                model.probe.data = t.as_tensor(data['probe']) / model.probe_norm
            elif ".cxi" in args['probefile']:
                data = readCXI(probefile).probe
                model.probe.data = t.as_tensor(data) / model.probe_norm
            model.probe.data = model.probe.data[0:args["n_modes"]]
        except:
            pass
    model.translation_offsets.data = t.rand_like(model.translation_offsets.data) * args['translation_randomization']
    return model

def center_probe(probe):
	# Make sure we dont screw with the input probe
	probe = t.clone(probe)
	for i in range(4):

		# Empirically, 4 iterations is repeatable to subpixel accuracy
		probe_abs_sq = t.sum(t.abs(probe) ** 2, axis=0)

		centroid = ip.centroid(probe_abs_sq)
		for i in range(probe.shape[0]):
			probe[i] = ip.sinc_subpixel_shift(probe[i],
											  (-centroid[0] + probe.shape[-2] / 2,
											   -centroid[1] + probe.shape[-1] / 2))
	return probe

def save_results(save_filename, model, dataset):
	results = model.save_results(dataset)
	results['wavelength'] = np.array(model.wavelength.cpu().numpy())
	results['oversampling'] = np.array(model.oversampling.cpu().numpy())
	print("[CDTOOLS] Saving results into file %s" %save_filename)
	io.savemat(save_filename, results)
