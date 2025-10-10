"""
Statistical analysis tools for Bluesky experiments.

This module provides functions to compute statistics and analyze data
from completed runs.
"""

import numpy as np
import pandas as pd
from scipy import stats


def analyze_run(run, signal_key):
    """
    Compute comprehensive statistics for a signal in a run.

    Parameters
    ----------
    run : BlueskyRun
        Run object from databroker
    signal_key : str
        Name of the signal to analyze

    Returns
    -------
    dict
        Dictionary of statistical measures

    Examples
    --------
    >>> from databroker import Broker
    >>> db = Broker.named('temp')
    >>> run = db[-1]
    >>> stats = analyze_run(run, 'detector_value')
    >>> print(stats)
    """
    table = run.table()
    signal = table[signal_key].values

    result = {
        'mean': np.mean(signal),
        'std': np.std(signal),
        'min': np.min(signal),
        'max': np.max(signal),
        'median': np.median(signal),
        'peak_to_peak': np.ptp(signal),
        'var': np.var(signal),
        'rms': np.sqrt(np.mean(signal**2)),
        'skewness': stats.skew(signal),
        'kurtosis': stats.kurtosis(signal),
    }

    # Percentiles
    result['q25'] = np.percentile(signal, 25)
    result['q75'] = np.percentile(signal, 75)
    result['iqr'] = result['q75'] - result['q25']

    return result


def find_peaks(run, x_key, y_key, height=None, prominence=None, distance=None):
    """
    Find peaks in scan data.

    Parameters
    ----------
    run : BlueskyRun
        Run object from databroker
    x_key : str
        Name of the position/x-axis signal
    y_key : str
        Name of the signal to find peaks in
    height : float, optional
        Minimum peak height
    prominence : float, optional
        Minimum peak prominence
    distance : int, optional
        Minimum distance between peaks (in samples)

    Returns
    -------
    dict
        Dictionary containing peak information

    Examples
    --------
    >>> peaks = find_peaks(run, 'frequency', 'power',
    ...                    prominence=5, distance=10)
    >>> print(f"Found {len(peaks['positions'])} peaks")
    """
    from scipy.signal import find_peaks as scipy_find_peaks

    table = run.table()
    x = table[x_key].values
    y = table[y_key].values

    peaks_idx, properties = scipy_find_peaks(y, height=height,
                                             prominence=prominence,
                                             distance=distance)

    return {
        'peak_indices': peaks_idx,
        'peak_positions': x[peaks_idx],
        'peak_values': y[peaks_idx],
        'properties': properties,
        'num_peaks': len(peaks_idx),
    }


def compare_runs(runs, signal_key):
    """
    Compare statistics across multiple runs.

    Parameters
    ----------
    runs : list of BlueskyRun
        List of run objects from databroker
    signal_key : str
        Name of the signal to compare

    Returns
    -------
    DataFrame
        Pandas DataFrame with comparison statistics

    Examples
    --------
    >>> recent_runs = list(db.search(plan_name='frequency_scan'))[-5:]
    >>> comparison = compare_runs(recent_runs, 'power')
    >>> print(comparison)
    """
    stats_list = []

    for run in runs:
        stats_dict = analyze_run(run, signal_key)
        stats_dict['scan_id'] = run.metadata['start']['scan_id']
        stats_dict['uid'] = run.metadata['start']['uid'][:8]
        stats_dict['time'] = run.metadata['start']['time']

        # Add any plan-specific info
        if 'plan_args' in run.metadata['start']:
            for key, value in run.metadata['start']['plan_args'].items():
                stats_dict[f'plan_{key}'] = value

        stats_list.append(stats_dict)

    df = pd.DataFrame(stats_list)

    # Sort by time
    if 'time' in df.columns:
        df = df.sort_values('time')

    return df


def compute_correlation(run, x_key, y_key):
    """
    Compute correlation between two signals.

    Parameters
    ----------
    run : BlueskyRun
        Run object from databroker
    x_key : str
        First signal name
    y_key : str
        Second signal name

    Returns
    -------
    dict
        Correlation statistics

    Examples
    --------
    >>> corr = compute_correlation(run, 'frequency', 'power')
    >>> print(f"Pearson r: {corr['pearson_r']:.3f}")
    """
    table = run.table()
    x = table[x_key].values
    y = table[y_key].values

    pearson_r, pearson_p = stats.pearsonr(x, y)
    spearman_r, spearman_p = stats.spearmanr(x, y)

    return {
        'pearson_r': pearson_r,
        'pearson_p': pearson_p,
        'spearman_r': spearman_r,
        'spearman_p': spearman_p,
    }


def fit_polynomial(run, x_key, y_key, degree=2):
    """
    Fit polynomial to data.

    Parameters
    ----------
    run : BlueskyRun
        Run object from databroker
    x_key : str
        Independent variable
    y_key : str
        Dependent variable
    degree : int, optional
        Polynomial degree (default: 2)

    Returns
    -------
    dict
        Fit results including coefficients and residuals

    Examples
    --------
    >>> fit = fit_polynomial(run, 'frequency', 'power', degree=3)
    >>> print(f"Coefficients: {fit['coefficients']}")
    >>> print(f"R-squared: {fit['r_squared']:.4f}")
    """
    table = run.table()
    x = table[x_key].values
    y = table[y_key].values

    # Fit polynomial
    coeffs = np.polyfit(x, y, degree)
    poly = np.poly1d(coeffs)

    # Compute predictions and residuals
    y_pred = poly(x)
    residuals = y - y_pred

    # R-squared
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((y - np.mean(y))**2)
    r_squared = 1 - (ss_res / ss_tot)

    return {
        'coefficients': coeffs.tolist(),
        'polynomial': poly,
        'predictions': y_pred,
        'residuals': residuals,
        'r_squared': r_squared,
        'rmse': np.sqrt(np.mean(residuals**2)),
    }


def detect_outliers(run, signal_key, method='iqr', threshold=1.5):
    """
    Detect outliers in signal data.

    Parameters
    ----------
    run : BlueskyRun
        Run object from databroker
    signal_key : str
        Signal to analyze
    method : str, optional
        Outlier detection method: 'iqr' or 'zscore' (default: 'iqr')
    threshold : float, optional
        Threshold for outlier detection (default: 1.5 for IQR, 3 for z-score)

    Returns
    -------
    dict
        Outlier information

    Examples
    --------
    >>> outliers = detect_outliers(run, 'detector_value', method='iqr')
    >>> print(f"Found {outliers['num_outliers']} outliers")
    """
    table = run.table()
    signal = table[signal_key].values

    if method == 'iqr':
        q25, q75 = np.percentile(signal, [25, 75])
        iqr = q75 - q25
        lower_bound = q25 - threshold * iqr
        upper_bound = q75 + threshold * iqr
        outlier_mask = (signal < lower_bound) | (signal > upper_bound)

    elif method == 'zscore':
        z_scores = np.abs(stats.zscore(signal))
        outlier_mask = z_scores > threshold

    else:
        raise ValueError(f"Unknown method: {method}")

    return {
        'outlier_indices': np.where(outlier_mask)[0],
        'outlier_values': signal[outlier_mask],
        'num_outliers': np.sum(outlier_mask),
        'outlier_fraction': np.mean(outlier_mask),
        'method': method,
        'threshold': threshold,
    }


def compute_snr(run, signal_key, noise_key=None):
    """
    Compute signal-to-noise ratio.

    Parameters
    ----------
    run : BlueskyRun
        Run object from databroker
    signal_key : str
        Signal channel name
    noise_key : str, optional
        Noise channel name (if None, estimates from signal std)

    Returns
    -------
    dict
        SNR statistics

    Examples
    --------
    >>> snr = compute_snr(run, 'detector_signal', 'detector_noise')
    >>> print(f"SNR: {snr['snr_db']:.1f} dB")
    """
    table = run.table()
    signal = table[signal_key].values

    signal_power = np.mean(signal**2)

    if noise_key:
        noise = table[noise_key].values
        noise_power = np.mean(noise**2)
    else:
        # Estimate noise from high-frequency components
        noise_power = np.var(signal)

    snr_linear = signal_power / noise_power if noise_power > 0 else np.inf
    snr_db = 10 * np.log10(snr_linear) if snr_linear > 0 else -np.inf

    return {
        'snr_linear': snr_linear,
        'snr_db': snr_db,
        'signal_power': signal_power,
        'noise_power': noise_power,
    }


def summarize_run(run):
    """
    Create comprehensive summary of a run.

    Parameters
    ----------
    run : BlueskyRun
        Run object from databroker

    Returns
    -------
    dict
        Complete run summary

    Examples
    --------
    >>> summary = summarize_run(run)
    >>> print(summary)
    """
    table = run.table()
    start = run.metadata['start']

    # Basic metadata
    summary = {
        'scan_id': start['scan_id'],
        'uid': start['uid'][:8],
        'plan_name': start['plan_name'],
        'operator': start.get('operator', 'unknown'),
        'purpose': start.get('purpose', 'N/A'),
        'timestamp': start['time'],
        'num_events': len(table),
    }

    # Analyze numeric columns
    numeric_cols = table.select_dtypes(include=[np.number]).columns.tolist()

    for col in numeric_cols[:3]:  # Limit to first 3 numeric columns
        stats = analyze_run(run, col)
        summary[f'{col}_stats'] = {
            'mean': stats['mean'],
            'std': stats['std'],
            'min': stats['min'],
            'max': stats['max'],
        }

    return summary
