import os
import sys
import numpy as np
from scipy.io import loadmat
import matplotlib.pyplot as plt; #plt.rcParams['figure.figsize'] = [15, 15]


def show_results(data, basedir, n):
    im = data['obj'][n:-n,n:-n]
    probe = data['probe']
    translation = data['translations']
    weights = data['weights']
    basis = data['obj_basis']

    print("Reconstructed pixel size: %4.f nm" %(np.abs(data["obj_basis"][0,1])*1e9))
    print("X-ray energy: %.4f" %(1239.8/data["wavelength"]/1e9))

    #### TEMP cut the image
    N = len(im)
    im_sub = im#[int(0.1*N):int(0.25*N),int(0.55*N):int(0.8*N)]

    plot_amplitude(im_sub, basis=basis, units='um', title='Object Amplitude').savefig(os.path.join(basedir, "amp.png"))
    plot_phase(im_sub, basis=basis, units='um', cmap='cividis', title='Object Phase').savefig(os.path.join(basedir, "phase.png"))
    #### TEMP
    for i in range(probe.shape[0]):
        plot_amplitude(probe[i],basis=basis, units='um', title='Probe Mode %d Amplitude'%i).savefig(os.path.join(basedir, f"probe_{i}.png"))
    plot_nanomap(translation, weights).savefig(os.path.join(basedir, "nano.png"))

def get_units_factor(units):
    """Gets the multiplicative factor associated with a length unit

    Parameters
    ----------
    units : str
        The abbreviation for the unit type

    Returns
    -------
    factor : float
        The factor meters / (unit)
    """

    u = units.lower()
    if u=='m':
        factor=1
    if u=='cm':
        factor=1e2
    if u=='mm':
        factor=1e3
    if u=='um' or u=="$\\mu$m":
        factor=1e6
    if u=='nm':
        factor=1e9
    if u=='a':
        factor=1e10
    if u=='pm':
        factor=1e12
    return factor


def plot_image(im, plot_func = lambda x : x, basis=None, units='$\\mu$m', cmap='viridis', cmap_label=None, interpolation=None, title=None, **kwargs):
    """Plots an image with a colorbar and on an appropriate spatial grid

    If a figure is given explicitly, it will clear that existing figure and
    plot over it. Otherwise, it will generate a new figure.

    If a basis is explicitly passed, the image will be plotted in real-space
    coordinates

    Finally, if a function is passed to the plot_func argument, this function
    will be called on each slice of data before it is plotted. This is used
    internally to enable the plot_real, plot_image, plot_phase, etc. functions.


    Parameters
    ----------
    im : array
        An complex array with dimensions NxM
    plot_func : callable
        A function which maps numpy arrays to the image to be plotted
    fig : matplotlib.figure.Figure
        Default is a new figure, a matplotlib figure to use to plot
    basis : np.array
        Optional, the 3x2 probe basis
    units : str
        The length units to mark on the plot, default is um
    cmap : str
        Default is 'viridis', the colormap to plot with
    cmap_label : str
        What to label the colorbar when plotting
    interpolation : str
        What interpolation to use for imshow
    \\**kwargs
        All other args are passed to fig.add_subplot(111, \\**kwargs)

    Returns
    -------
    used_fig : matplotlib.figure.Figure
        The figure object that was actually plotted to.
    """

    fig = plt.figure()
    # If im only has two dimensions, this reshape will add a leading
    # dimension, and update will be called on index 0. If it has 3 or more
    # dimensions, then all the leading dimensions will be compressed into
    # one long dimension which can be scrolled through.
    s = im.shape
    to_plot = plot_func(im.reshape(-1,s[-2],s[-1])[0])

    #Plot in a basis if it exists, otherwise dont
    if basis is not None:
        np_basis = basis
        # This fails if the basis is not rectangular
        basis_norm = np.linalg.norm(np_basis, axis = 0)
        basis_norm = basis_norm * get_units_factor(units)

        extent = [0, im.shape[-1]*basis_norm[1], 0,
                  im.shape[-2]*basis_norm[0]]
    else:
        extent=None

    plt.imshow(to_plot, cmap = cmap, extent = extent, interpolation=interpolation)
    cbar = plt.colorbar()
    if cmap_label is not None:
        cbar.set_label(cmap_label)

    if basis is not None:
        plt.xlabel('X (' + units + ')')
        plt.ylabel('Y (' + units + ')')
    else:
        plt.xlabel('j (pixels)')
        plt.ylabel('i (pixels)')
    
    plt.title(title)
    return fig

def plot_real(im, basis=None, units='$\\mu$m', cmap='viridis', cmap_label='Real Part (a.u.)', **kwargs):
    """Plots the real part of a complex array with dimensions NxM

    If a figure is given explicitly, it will clear that existing figure and
    plot over it. Otherwise, it will generate a new figure.

    If a basis is explicitly passed, the image will be plotted in real-space
    coordinates

    Parameters
    ----------
    im : array
        An complex array with dimensions NxM
    fig : matplotlib.figure.Figure
        Default is a new figure, a matplotlib figure to use to plot
    basis : np.array
        Optional, the 3x2 probe basis
    units : str
        The length units to mark on the plot, default is um
    cmap : str
        Default is 'viridis', the colormap to plot with
    cmap_label : str
        What to label the colorbar when plotting
    \\**kwargs
        All other args are passed to fig.add_subplot(111, \\**kwargs)

    Returns
    -------
    used_fig : matplotlib.figure.Figure
        The figure object that was actually plotted to.
    """
    plot_func = lambda x: np.real(x)
    return plot_image(im, plot_func=plot_func, basis=basis,
                      units=units, cmap=cmap, cmap_label=cmap_label,
                      **kwargs)



def plot_imag(im, basis=None, units='$\\mu$m', cmap='viridis', cmap_label='Imaginary Part (a.u.)', **kwargs):
    """Plots the imaginary part of a complex array with dimensions NxM

    If a figure is given explicitly, it will clear that existing figure and
    plot over it. Otherwise, it will generate a new figure.

    If a basis is explicitly passed, the image will be plotted in real-space
    coordinates

    Parameters
    ----------
    im : array
        An complex array with dimensions NxM
    fig : matplotlib.figure.Figure
        Default is a new figure, a matplotlib figure to use to plot
    basis : np.array
        Optional, the 3x2 probe basis
    units : str
        The length units to mark on the plot, default is um
    cmap : str
        Default is 'viridis', the colormap to plot with
    cmap_label : str
        What to label the colorbar when plotting
    \\**kwargs
        All other args are passed to fig.add_subplot(111, \\**kwargs)

    Returns
    -------
    used_fig : matplotlib.figure.Figure
        The figure object that was actually plotted to.
    """
    plot_func = lambda x: np.imag(x)
    return plot_image(im, plot_func=plot_func, basis=basis,
                      units=units, cmap=cmap, cmap_label=cmap_label,
                      **kwargs)


def plot_amplitude(im, basis=None, units='$\\mu$m', cmap='viridis', cmap_label='Amplitude (a.u.)', **kwargs):
    """Plots the amplitude of a complex array with dimensions NxM

    If a figure is given explicitly, it will clear that existing figure and
    plot over it. Otherwise, it will generate a new figure.

    If a basis is explicitly passed, the image will be plotted in real-space
    coordinates.

    Parameters
    ----------
    im : array
        An complex array with dimensions NxM
    fig : matplotlib.figure.Figure
        Default is a new figure, a matplotlib figure to use to plot
    basis : np.array
        Optional, the 3x2 probe basis
    units : str
        The length units to mark on the plot, default is um
    cmap : str
        Default is 'viridis', the colormap to plot with
    cmap_label : str
        What to label the colorbar when plotting
    \\**kwargs
        All other args are passed to fig.add_subplot(111, \\**kwargs)

    Returns
    -------
    used_fig : matplotlib.figure.Figure
        The figure object that was actually plotted to.
    """
    plot_func = lambda x: np.absolute(x)#.clip(max=0.5)
    return plot_image(im, plot_func=plot_func, basis=basis,
                      units=units, cmap=cmap, cmap_label=cmap_label,
                      **kwargs)


def plot_phase(im, basis=None, units='$\\mu$m', cmap='auto', cmap_label='Phase (rad)', **kwargs):
    """ Plots the phase of a complex array with dimensions NxMx2

    If a figure is given explicitly, it will clear that existing figure and
    plot over it. Otherwise, it will generate a new figure.

    If a basis is explicitly passed, the image will be plotted in real-space
    coordinates

    Parameters
    ----------
    im : array
        An complex array with dimensions NxM
    fig : matplotlib.figure.Figure
        Default is a new figure, a matplotlib figure to use to plot
    basis : np.array
        Optional, the 3x2 probe basis
    units : str
        The length units to mark on the plot, default is um
    cmap : str
        Default is 'viridis', the colormap to plot with
    cmap_label : str
        What to label the colorbar when plotting
    \\**kwargs
        All other args are passed to fig.add_subplot(111, \\**kwargs)

    Returns
    -------
    used_fig : matplotlib.figure.Figure
        The figure object that was actually plotted to.
    """
    if cmap == 'auto':
        if 'twilight' in plt.colormaps():
            cmap = 'twilight'
        elif 'hsv' in plt.colormaps():
            cmap = 'hsv'
        else:
            raise AttributeError('Neither twilight or hsv colormap exists in this screwed up matplotlib install')

    plot_func = lambda x: np.angle(x)
    return plot_image(im, plot_func=plot_func, basis=basis,
                      units=units, cmap=cmap, cmap_label=cmap_label,
                      **kwargs)

def plot_translations(translations, units='$\\mu$m', lines=True, invert_xaxis=True, **kwargs):
    """Plots a set of probe translations in a nicely formatted way

    Parameters
    ----------
    translations : array
        An Nx2 or Nx3 set of translations in real space
    fig : matplotlib.figure.Figure
        Default is a new figure, a matplotlib figure to use to plot
    units : str
        Default is um, units to report in (assuming input in m)
    lines : bool
        Whether to plot lines indicating the path taken
    invert_xaxis : bool
        Default is True. This flips the x axis to match the convention from .cxi files of viewing the image from the beam's perspective
    \\**kwargs
        All other args are passed to fig.add_subplot(111, \\**kwargs)


    Returns
    -------
    used_fig : matplotlib.figure.Figure
        The figure object that was actually plotted to.
    """

    factor = get_units_factor(units)

    fig = plt.figure()
    ax = fig.add_subplot(111, **kwargs)

    translations = translations * factor
    plt.plot(translations[:,0], translations[:,1],'k.')
    if invert_xaxis:
        plt.gca().invert_xaxis()
        
    if lines:
        plt.plot(translations[:,0], translations[:,1],'b-', linewidth=0.5)
    plt.xlabel('X (' + units + ')')
    plt.ylabel('Y (' + units + ')')

    return fig


def plot_nanomap(translations, values, units='$\\mu$m', convention='probe', invert_xaxis=True, **kwargs):
    """Plots a set of nanomap data in a flexible way

    Parameters
    ----------
    translations : array
        An Nx2 or Nx3 set of translations in real space
    values : array
        A length-N object of values associated with the translations
    fig : matplotlib.figure.Figure
        Default is a new figure, a matplotlib figure to use to plot
    units : str
        Default is um, units to report in (assuming input in m)
    convention : str
        Default is 'probe', alternative is 'obj'. Whether the translations refer to the probe or object.
    invert_xaxis : bool
        Default is True. This flips the x axis to match the convention from .cxi files of viewing the image from the beam's perspective

    Returns
    -------
    used_fig : matplotlib.figure.Figure
        The figure object that was actually plotted to.
    """

    fig = plt.figure()
    ax = fig.add_subplot(111, **kwargs)
    
    factor = get_units_factor(units)

    bbox = fig.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    trans = np.array(translations)
    values = np.array(values)

    if convention.lower() != 'probe':
        trans = trans * -1

    s = bbox.width * bbox.height / trans.shape[0] * 72**2 #72 is points per inch
    s /= 4 # A rough value to make the size work out

    plt.scatter(factor * trans[:,0],factor * trans[:,1],s=s,c=values)
    if invert_xaxis:
        plt.gca().invert_xaxis()
    
    plt.gca().set_facecolor('k')
    plt.xlabel('Translation x (' + units + ')')
    plt.ylabel('Translation y (' + units + ')')
    plt.colorbar()

    return fig

if __name__ == "__main__":
    input_file = sys.argv[1]
    data = loadmat(input_file)
    n = 440
    show_results(data, n)
    plt.show()
