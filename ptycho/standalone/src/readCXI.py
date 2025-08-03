__author__ = 'davidshapiro'

import os, h5py
import datetime
import numpy as np
import scipy as sc
from skimage.restoration import unwrap_phase

from errno import ENOENT
from param import Param
from general import e2l, l2e, removePlane, polyfit2d, polyval2d
from general import filtered_auto, getIOMask, getPhaseMask, getIOSpectrum, convert2OD, getPhaseShift
from STXM_reader_utils import *

class cxi(object):

    def __init__(self, cxiFile = None, loaddiff = True):

        self.beamline = 'COSMIC'
        self.facility = 'ALS'
        self.energy = 1000
        self.ccddata = 0
        self.probe = 0
        self.imageProbe = 0
        self.probemask = 0 ##Fourier mask
        self.probeRmask = 0 ##Real space mask
        self.illuminationIntensities = 0
        self.datamean = 0
        self.stxm = 0
        self.stxmInterp = 0
        self.xpixelsize = 0
        self.ypixelsize = 0
        self.translation = 0
        self.image = 0
        self.startImage = 0
        self.bg = 0
        self.beamstop = 0
        self.corner_x = 0
        self.corner_y = 0
        self.corner_z = 0
        self.process = 0
        self.time = 0
        self.indices = 0
        self.goodFrames = 0
        self.corner = 0
        self.indices = 0
        self.error = 0
        self.__delta = 0.0001

        if cxiFile == None:
            self.process = Param().param
        else:
            # try: f = h5py.File(cxiFile,'r')
            # except IOError:
            #     print("readCXI Error: no such file or directory")
            #     #return
            if not os.path.isfile(cxiFile):
                raise IOError(ENOENT, 'No such file', cxiFile)
            else:
                f = h5py.File(cxiFile,'r')
                print("Loading file contents...")
                try: self.beamline = f['entry_1/instrument_1/name'][()]
                except KeyError: self.beamline = None
                try: self.facility = f['entry_1/instrument_1/source_1/name'][()]
                except KeyError: self.facility = None
                try:
                    self.energy = f['entry_1/instrument_1/source_1/energy'][()]
                except KeyError:
                    self.energy = None
                if loaddiff:
                    try: self.ccddata = f['/entry_1/instrument_1/detector_1/data'][()]
                    except KeyError:
                        print("Could not locate CCD data!")
                        self.ccddata = None
                else: self.ccddata = None
                try: self.probemask = f['entry_1/instrument_1/detector_1/probe_mask'][()]
                except KeyError: self.probemask = None
                try: self.probeRmask = f['entry_1/instrument_1/detector_1/probe_Rmask'][()]
                except KeyError: self.probeRmask = None
                try: self.datamean = f['entry_1/instrument_1/detector_1/Data Average'][()]
                except KeyError: self.datamean = None
                try: self.stxm = f['entry_1/instrument_1/detector_1/STXM'][()]
                except KeyError: self.stxm = None
                try: self.stxmInterp = f['entry_1/instrument_1/detector_1/STXMInterp'][()]
                except KeyError: self.stxmInterp = None
                try: self.ccddistance = f['entry_1/instrument_1/detector_1/distance'][()]
                except KeyError: self.ccddistance = None
                try: self.xpixelsize = f['entry_1/instrument_1/detector_1/x_pixel_size'][()]
                except KeyError: self.xpixelsize = None
                try: self.ypixelsize = f['entry_1/instrument_1/detector_1/y_pixel_size'][()]
                except KeyError: self.ypixelsize = None
                try: self.translation = f['entry_1/instrument_1/detector_1/translation'][()]
                except KeyError: self.translation = None
                try: self.illuminationIntensities = f['entry_1/instrument_1/detector_1/illumination_intensities'][()]
                except KeyError: self.illuminationIntensities = None


                entryList = [str(e) for e in list(f['entry_1'])]
                currentImageNumber = str(len([e for e in list(f['entry_1']) if 'image' in e and 'latest' not in e]))

                # if 'image_latest' in entryList:
                #     image_offset = 2
                # else: image_offset = 0
                # try: currentImageNumber = str(max(loc for loc, val in enumerate(entryList) if not(val.rfind('image'))) - image_offset)
                # except:
                if currentImageNumber == '0':
                    print("Could not locate ptychography image data.")
                    self.image = None
                    try: self.probe = f['entry_1/instrument_1/detector_1/probe'][()]
                    except KeyError: self.probe = None
                    self.imageProbe = self.probe
                    self.bg = None
                else:
                    print("Found %s images" %(int(currentImageNumber)))
                    self.image = []
                    for i in range(1,int(currentImageNumber) + 1):
                        print("loading image: %s" %(i))
                        try:
                            #self.image.append(f['entry_1/image_' + str(i) + '/data_' + str(i) + '/data'][()])
                            self.image.append(f['entry_1/image_'+str(i)+'/data'][()])
                        except:
                            pass
                    try: self.probe = f['entry_1/image_' + currentImageNumber + '/process_1/final_illumination'][()]
                    except: self.probe = None
                    # except:
                    #     try: self.imageProbe = f['entry_1/instrument_1/detector_1/probe'][()]
                    #     except KeyError:
                    #         try: self.imageProbe = f['entry_1/instrument_1/detector_1/Probe'][()]
                    #         except KeyError:
                    #             self.imageProbe = None
                    try: self.bg = f['entry_1/image_' + currentImageNumber + '/process_1/final_background'][()]
                    except: self.bg = None
                    #self.imageProbe = f['entry_1/image_1/process_1/final_illumination'][()]
                    #self.probe = self.imageProbe.copy()
                    
                
                try: self.dataProbe = f['entry_1/instrument_1/source_1/data_illumination'][()]
                except KeyError: self.dataProbe = None
                try: self.startImage = f['entry_1/image_1/startImage'][()]
                except KeyError: self.startImage = None
                try: self.beamstop = f['entry_1/instrument_1/detector_1/Beamstop'][()]
                except KeyError: self.beamstop = None
                try:
                    self.corner_x,self.corner_y,self.corner_z = f['/entry_1/instrument_1/detector_1/corner_position'][()]
                except:
                    try:
                        self.corner_z = f['entry_1/instrument_1/detector_1/distance'][()]
                        self.corner_y = f['entry_1/instrument_1/detector_1/y_pixel_size'][()] * self.probe.shape[0] / 2.
                        self.corner_x = f['entry_1/instrument_1/detector_1/x_pixel_size'][()] * self.probe.shape[1] / 2.
                    except:
                        self.corner_x,self.corner_y,self.corner_z = None, None, None

                self.process = Param().param
                if 'entry_1/process_1/Param' in f:
                    for item in list(f['entry_1/process_1/Param']):
                        self.process[str(item)] = str(f['/entry_1/process_1/Param/'+str(item)][()])
                try: self.time = f['entry_1/start_time'][()]
                except KeyError: self.time = None
                try: self.indices = f['entry_1/process_1/indices'][()]
                except KeyError: self.indices = None
                try: self.goodFrames = f['entry_1/process_1/good frames'][()]
                except KeyError: self.goodFrames = None
                # if 'entry_1/image_latest' in f:
                #     self.probe = f['entry_1/image_latest/process_1/final_illumination/'] #f['entry_1/image_1/probe'][()]
                if '/entry_1/instrument_1/detector_1/corner_position' in f:
                    self.corner = f['/entry_1/instrument_1/detector_1/corner_position'][()]
                else: self.corner = None
                f.close()

    def help(self):
        print("Usage: cxi = readCXI(fileName)")
        print("cxi.beamline = beamline name")
        print("cxi.facility = facility name")
        print("cxi.energy = energy in joules")
        print("cxi.ccddata = stack of diffraction data")
        print("cxi.probe = current probe")
        print("cxi.dataProbe = probe estimated from the data")
        print("cxi.imageProbe = probe calculated from the reconstruction")
        print("cxi.probemask = probe mask calculated from diffraction data")
        print("cxi.datamean = average diffraction pattern")
        print("cxi.stxm = STXM image calculated from diffraction data")
        print("cxi.stxmInterp = STXM image interpolated onto the reconstruction grid")
        print("cxi.xpixelsize = x pixel size in meters")
        print("cxi.ypixelsize = y pixel size in meters")
        print("cxi.translation = list of sample translations in meters")
        print("cxi.image = reconstructed image")
        print("cxi.bg = reconstructed background")
        print("cxi.process = parameter list used by the pre-processor")
        print("cxi.time = time of pre-processing")
        print("cxi.indices = array of STXM pixel coordinates for each dataset")
        print("cxi.goodFrames = boolean array indicating good frames")
        print("cxi.startImage = image which started the iteration")
        print("cxi.corner_x/y/z = positions of the CCD corner")

    def generateSTXM(self, hdr = None, pts = None, threshold = 0.1, mode = 'roi', roi=(-100,-1,0,50)):
        if hdr is not None:
            hdr = Read_header(hdr)
            ypts, xpts = hdr['Region1']['nypoints'], hdr['Region1']['nxpoints']
            if mode == 'full':
                iPoints = (self.ccddata * (self.ccddata > threshold)).sum(axis = (1,2))
            elif mode == 'brightfield':
                mask = self.datamean > 0.1 * self.datamean.max()
                iPoints = (self.ccddata * mask).sum(axis = (1,2))
            elif mode == 'darkfield':
                mask = self.datamean < 0.1 * self.datamean.max()
                iPoints = (self.ccddata * mask).sum(axis = (1,2))
            elif mode == 'roi':
                mask = np.zeros(self.ccddata[0].shape)
                mask[roi[0]:roi[1],roi[2]:roi[3]] = 1
                iPoints = (self.ccddata * mask).mean(axis = (1,2))
            self.stxm = np.reshape(iPoints,(ypts,xpts))[::-1,:]
        elif pts is not None:
            ypts, xpts = pts
            if mode == 'full':
                iPoints = (self.ccddata * (self.ccddata > threshold)).sum(axis = (1,2))
            elif mode == 'brightfield':
                mask = self.datamean > 0.1 * self.datamean.max()
                iPoints = (self.ccddata * mask).sum(axis = (1,2))
            elif mode == 'darkfield':
                mask = self.datamean < 0.1 * self.datamean.max()
                iPoints = (self.ccddata * mask).sum(axis = (1,2))
            self.stxm = np.reshape(iPoints,(ypts,xpts))[::-1,:]
        else:
            print("Please input a header file for the ptychography scan")

    def pixnm(self):

        l = (1239.852 / (self.energy / 1.602e-19)) * 1e-9
        NA = np.sqrt(self.corner_x**2 + self.corner_y**2) / np.sqrt(2.) / self.corner_z
        return np.round(l / 2. / NA * 1e9,2)

    def ev(self):
        return np.round(self.energy * 6.242e18,2)

    def removeOutliers(self, sigma = 3):

        nPoints = len(self.translation)
        indx = self.indices
        ny, nx = self.stxm.shape
        gy, gx = np.gradient(self.stxm)

        gy = self.stxm - sc.ndimage.filters.gaussian_filter(self.stxm, sigma = 0.25)
        gy = gy[::-1,:].flatten()  ##puts it in the same ordering as ccddata, starting lower left
        delta = 8. * gy.std()
        badIndices = np.where(gy < (gy.mean() - delta))[0] ##the min Y gradient is one row below the bad pixel

        self.stxm = self.stxm[::-1,:].flatten()
        k = 0
        if len(badIndices) > 0:
            for item in badIndices:
                self.stxm[item] = (self.stxm[item + 1] + self.stxm[item - 1]) / 2.
                if indx[item] > 0:
                    indx[item] = 0
                    indx[item+1:nPoints] = indx[item+1:nPoints] - 1
                else: indx[item] = 0
                self.translation = np.delete(self.translation, item - k, axis = 0)
                self.ccddata = np.delete(self.ccddata, item - k, axis = 0)
                k += 1
        self.stxm = np.reshape(self.stxm,(ny,nx))[::-1,:]
        print("Removed %i bad frames." %(len(badIndices)))

    def imageShape(self):

        ny, nx = self.ccddata[0].shape
        pixm = self.pixnm() / 1e9
        y,x = np.array((self.translation[:,1], self.translation[:,0]))
        y = (y / pixm).round() + ny / 2
        x = (x / pixm).round() + nx / 2
        pPosVec = np.column_stack((y,x))

        dx = pPosVec[:,1].max() - pPosVec[:,1].min() + 2
        dy = pPosVec[:,0].max() - pPosVec[:,0].min() + 2

        return np.int(dy + ny), np.int(dx + nx)

    def pixelTranslations(self):

        pixm = self.pixnm() / 1e9
        ny, nx = self.ccddata[0].shape
        y,x = np.array((self.translation[:,1], self.translation[:,0]))
        y = (y / pixm).round() + ny / 2
        x = (x / pixm).round() + nx / 2
        return np.column_stack((y,x))

    def dataShape(self):

        return self.ccddata.shape

    def illumination(self):

        """
        Public function which computes the overlap from a stack of probes.  This is equivalent to the total illumination profile
        Input: Stack translation indices and the probe
        Output: Illumination profile
        """
        #TODO: verify that this is correct for multimode
        # isum = np.zeros(self.oSum.shape)
        # for k in range(self.oModes):
        #     for i in range(self.__nFrames):
        #         j = self.__indices[i]
        #         isum[k,j[0]:j[1],j[2]:j[3]] = isum[k,j[0]:j[1],j[2]:j[3]] + np.reshape(abs(self.probe.sum(axis = 1)), (self.ny, self.nx))
        # return isum
        qnorm = np.abs(self.QPH(self.QP(np.ones(self.ccddata.shape, complex))))
        print(qnorm.sum())
        return self.QH(qnorm/qnorm[0].sum()) + self.__delta**2

    def QP(self, o):

        """
        Private function which multiplies the frames by the probe
        Input: stack of frames
        Output: stack of frames times the probe
        """

        return o * self.probe

    def QPH(self, o):

        """
        Private function which multiplies the frames by the conjugate probe.
        Input: stack of frames
        Output: stack of frames times the conjugate probe
        """

        return o * self.probe.conjugate()

    def QH(self, ovec):

        """
        Private function which computes the overlap from stack of frames.
        Input: Stack translation indices and the stack of frames
        Output: Total object image
        """
        self.ny, self.nx = self.probe.shape
        self.__indices = []
        i = 0
        for p in self.pixelTranslations():
            x1 = np.int(p[1] - self.nx / 2.)
            x2 = np.int(p[1] + self.nx / 2.)
            y1 = np.int(p[0] - self.ny / 2.)
            y2 = np.int(p[0] + self.ny / 2.)
            self.__indices.append((y1,y2,x1,x2))
            i += 1

        osum = np.zeros(self.imageShape())  ##this is 3D, (oModes, oSizeY, oSizeX)

        for i in range(len(self.ccddata)):
            j = self.__indices[i]
            ##sum the oVec over the probe modes and then insert into the oSum maintaining separation
            ##of the object modes
            osum[j[0]:j[1], j[2]:j[3]] = osum[j[0]:j[1], j[2]:j[3]] + ovec[i,:,:]

        return osum

    def getod(self):
        """optical density"""
        mod = np.abs(self.image[-1])
        mask = self.getmask()
        IO = (mod * mask)[mask > 0].mean()
        self.od = convert2OD(mod, IO)
        return self.od

    def getpc(self, removeRamp = False, order = 1):
        """phase contrast"""
        self.pc = unwrap_phase(-np.log(self.image[-1]).imag)

        if removeRamp:
            mask = self.getmask()
            x,y = np.arange(0, self.pc.shape[1]),np.arange(0,self.pc.shape[0])
            xp,yp = np.meshgrid(x,y)
            xm,ym,zm = xp[mask], yp[mask], self.pc[mask]
            m = polyfit2d(xm,ym,zm,order = order)
            bgFit = polyval2d(xp.astype('float64'),yp.astype('float64'),m)
            self.pc = self.pc + bgFit

        self.pc -= self.pc.min()
        return self.pc

    def getsc(self, removeRamp = False, order = 1):
        """scattering contrast - just an estimate since it only really works for isolated particles"""
        """Need a smooth open background"""
        print("Calculation scattering contrast")
        self.pc = unwrap_phase(-np.log(self.image[-1]).imag) #self.getpc(removeRamp = removeRamp, order = order)
        self.od = self.getod()
        self.sc = np.sqrt(self.od**2 + self.pc**2)
        return self.sc

    def getmask(self, sigma = 3):

        self.mask = getIOMask(sc.ndimage.filters.gaussian_filter(np.abs(self.image[-1]) / np.abs(self.image[-1]).max(), sigma = sigma))
        return self.mask

def readCXI(cxiFile, loaddiff = False):

    cxiObj = cxi(cxiFile, loaddiff = loaddiff)

    return cxiObj

def placeProbe(cxiFile, probe):

    """
    Places probe in detector_1 group of the cxiFile
    """
    f = h5py.File(cxiFile, 'r+')
    del f['entry_1/instrument_1/detector_1/probe']
    del f['entry_1/instrument_1/detector_1/data_illumination']
    dset = f.create_dataset('entry_1/instrument_1/detector_1/probe', data = probe)
    dset = f.create_dataset('entry_1/instrument_1/detector_1/data_illumination', data = probe)
    f.close()

def placeIntensities(cxiFile, intensities):

    """
    Places probe in detector_1 group of the cxiFile
    """
    f = h5py.File(cxiFile, 'a')
    del f['entry_1/instrument_1/detector_1/illumination_intensities']
    dset = f.create_dataset('entry_1/instrument_1/detector_1/illumination_intensities', data = intensities)


    f.close()

def writeCXI(cxiObj, fileName = None):

    if fileName == None:
        if cxiObj.process['dataFile'] == '':
            print("writeCXI Error: no data file given.")
            print("Usage: writeCXI(cxiObj, fileName = None)")
            return 1
        else: fileName = cxiObj.process['scanDir'] + cxiObj.process['dataFile']

    f = h5py.File(fileName, "w")
    f.create_dataset("cxi_version",data = 130)
    entry_1 = f.create_group("entry_1")
    entry_1.create_dataset("start_time",data=datetime.date.today().isoformat())

    instrument_1 = entry_1.create_group("instrument_1")
#    instrument_1.create_dataset("name",data=cxiObj.beamline)
    source_1 = instrument_1.create_group("source_1")
    source_1.create_dataset("energy", data=cxiObj.energy) # in J
    source_1.create_dataset("name",data="ALS")
    source_1.create_dataset("probe_mask", data = cxiObj.probemask)
    source_1.create_dataset("probe", data = cxiObj.probe)
    source_1.create_dataset("data_illumination", data = cxiObj.probe)

    detector_1 = instrument_1.create_group("detector_1")
    detector_1.create_dataset("data", data= cxiObj.ccddata.astype('float32'),compression='gzip')
    detector_1['data'].attrs['axes'] = "translation:y:x"
    detector_1.create_dataset("probe", data = cxiObj.probe)
    detector_1.create_dataset("data_illumination", data = cxiObj.probe)
#    detector_1.create_dataset("illumination_intensities", data = cxiObj.illuminationIntensities)
    detector_1.create_dataset("probe_mask", data = cxiObj.probemask)
#    detector_1.create_dataset("probe_Rmask", data = cxiObj.probeRmask)
#    detector_1.create_dataset("Data Average", data = cxiObj.datamean)
#    detector_1.create_dataset("STXM", data = cxiObj.stxm)
#    detector_1.create_dataset("STXMInterp", data = cxiObj.stxmInterp)
    detector_1.create_dataset("distance", data=cxiObj.corner_z) # in meters
    detector_1["translation"] = h5py.SoftLink('/entry_1/sample_1/geometry_1/translation')
    detector_1.create_dataset("x_pixel_size", data = cxiObj.xpixelsize) # in meters
    detector_1.create_dataset("y_pixel_size", data = cxiObj.ypixelsize) # in meters
    detector_1.create_dataset("corner_position", data = (cxiObj.corner_x, cxiObj.corner_y, cxiObj.corner_z)) # in meters
    sample_1 = entry_1.create_group("sample_1")
    geometry_1 = sample_1.create_group("geometry_1")
    geometry_1.create_dataset("translation", data = cxiObj.translation)

    data_1 = entry_1.create_group("data_1")
    data_1["data"] = h5py.SoftLink('/entry_1/instrument_1/detector_1/data')
    data_1["translation"] = h5py.SoftLink('/entry_1/sample_1/geometry_1/translation')

#    process_1 = entry_1.create_group("process_1")
#    process_1.create_dataset("command",data=" ")
#    process_1.create_dataset("indices", data = cxiObj.indices)
#    paramGroup = process_1.create_group('Param')
#    dsets = []
#    for item in cxiObj.process:
#        dsets.append(paramGroup.create_dataset(item, data = cxiObj.process[item]))
    f.close()
    return 0
