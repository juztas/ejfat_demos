#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: FM Digital Sideband Detector (SDR to E2SAR)
# Description: FM receiver with digital sideband detection and E2SAR streaming
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import blocks
from gnuradio import ejfat
from gnuradio import eng_notation
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from xmlrpc.server import SimpleXMLRPCServer
import threading
import osmosdr
import time
import sip



class fm_digital_detector_e2sar(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "FM Digital Sideband Detector (SDR to E2SAR)", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("FM Digital Sideband Detector (SDR to E2SAR)")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "fm_digital_detector_e2sar")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.freq = freq = 106.1e6
        self.vlen = vlen = 8192
        self.upper_sideband_center = upper_sideband_center = 165000
        self.signal_level = signal_level = 0
        self.sideband_bw = sideband_bw = 70000
        self.samp_rate = samp_rate = 2400000
        self.lower_sideband_center = lower_sideband_center = -165000
        self.freq_display = freq_display = (freq/1e6)
        self.event_src_id = event_src_id = 1
        self.energy_avg_len = energy_avg_len = 10000
        self.ejfat_uri = ejfat_uri = "ejfat://127.0.0.1:19522/lb/1?data=127.0.0.1:19522"
        self.digital_threshold = digital_threshold = -20
        self.digital_indicator = digital_indicator = 0
        self.data_id = data_id = 1

        ##################################################
        # Blocks
        ##################################################

        self.blocks_probe_signal_1 = blocks.probe_signal_f()
        self.blocks_probe_signal_0 = blocks.probe_signal_f()
        self.xmlrpc_server_0 = SimpleXMLRPCServer(('localhost', 8080), allow_none=True)
        self.xmlrpc_server_0.register_instance(self)
        self.xmlrpc_server_0_thread = threading.Thread(target=self.xmlrpc_server_0.serve_forever)
        self.xmlrpc_server_0_thread.daemon = True
        self.xmlrpc_server_0_thread.start()
        def _signal_level_probe():
          self.flowgraph_started.wait()
          while True:

            val = self.blocks_probe_signal_1.level()
            try:
              try:
                self.doc.add_next_tick_callback(functools.partial(self.set_signal_level,val))
              except AttributeError:
                self.set_signal_level(val)
            except AttributeError:
              pass
            time.sleep(1.0 / (10))
        _signal_level_thread = threading.Thread(target=_signal_level_probe)
        _signal_level_thread.daemon = True
        _signal_level_thread.start()
        self.qtgui_waterfall_sink_x_0 = qtgui.waterfall_sink_c(
            1024, #size
            window.WIN_BLACKMAN, #wintype
            0, #fc
            samp_rate, #bw
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_waterfall_sink_x_0.set_update_time(0.10)
        self.qtgui_waterfall_sink_x_0.enable_grid(False)
        self.qtgui_waterfall_sink_x_0.enable_axis_labels(True)



        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        colors = [0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_waterfall_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_waterfall_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_waterfall_sink_x_0.set_color_map(i, colors[i])
            self.qtgui_waterfall_sink_x_0.set_line_alpha(i, alphas[i])

        self.qtgui_waterfall_sink_x_0.set_intensity_range(-140, 10)

        self._qtgui_waterfall_sink_x_0_win = sip.wrapinstance(self.qtgui_waterfall_sink_x_0.qwidget(), Qt.QWidget)

        self.top_layout.addWidget(self._qtgui_waterfall_sink_x_0_win)
        self.qtgui_number_sink_2 = qtgui.number_sink(
            gr.sizeof_float,
            0,
            qtgui.NUM_GRAPH_HORIZ,
            1,
            None # parent
        )
        self.qtgui_number_sink_2.set_update_time(0.10)
        self.qtgui_number_sink_2.set_title("")

        labels = ['FM Signal Level', '', '', '', '',
            '', '', '', '', '']
        units = ['dB', '', '', '', '',
            '', '', '', '', '']
        colors = [("blue", "red"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"),
            ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black")]
        factor = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]

        for i in range(1):
            self.qtgui_number_sink_2.set_min(i, -80)
            self.qtgui_number_sink_2.set_max(i, 0)
            self.qtgui_number_sink_2.set_color(i, colors[i][0], colors[i][1])
            if len(labels[i]) == 0:
                self.qtgui_number_sink_2.set_label(i, "Data {0}".format(i))
            else:
                self.qtgui_number_sink_2.set_label(i, labels[i])
            self.qtgui_number_sink_2.set_unit(i, units[i])
            self.qtgui_number_sink_2.set_factor(i, factor[i])

        self.qtgui_number_sink_2.enable_autoscale(False)
        self._qtgui_number_sink_2_win = sip.wrapinstance(self.qtgui_number_sink_2.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_number_sink_2_win)
        self.qtgui_number_sink_1 = qtgui.number_sink(
            gr.sizeof_float,
            0,
            qtgui.NUM_GRAPH_NONE,
            1,
            None # parent
        )
        self.qtgui_number_sink_1.set_update_time(0.10)
        self.qtgui_number_sink_1.set_title("")

        labels = ['Digital FM', '', '', '', '',
            '', '', '', '', '']
        units = ['(False if {value} == 0 else True)', '', '', '', '',
            '', '', '', '', '']
        colors = [("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"),
            ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black")]
        factor = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]

        for i in range(1):
            self.qtgui_number_sink_1.set_min(i, 0)
            self.qtgui_number_sink_1.set_max(i, 1)
            self.qtgui_number_sink_1.set_color(i, colors[i][0], colors[i][1])
            if len(labels[i]) == 0:
                self.qtgui_number_sink_1.set_label(i, "Data {0}".format(i))
            else:
                self.qtgui_number_sink_1.set_label(i, labels[i])
            self.qtgui_number_sink_1.set_unit(i, units[i])
            self.qtgui_number_sink_1.set_factor(i, factor[i])

        self.qtgui_number_sink_1.enable_autoscale(False)
        self._qtgui_number_sink_1_win = sip.wrapinstance(self.qtgui_number_sink_1.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_number_sink_1_win)
        self.qtgui_number_sink_0 = qtgui.number_sink(
            gr.sizeof_float,
            0,
            qtgui.NUM_GRAPH_HORIZ,
            2,
            None # parent
        )
        self.qtgui_number_sink_0.set_update_time(0.10)
        self.qtgui_number_sink_0.set_title("Sideband Power (dB relative to FM)")

        labels = ['Lower Sideband', 'Upper Sideband', '', '', '',
            '', '', '', '', '']
        units = ['dB', 'dB', '', '', '',
            '', '', '', '', '']
        colors = [("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"),
            ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black")]
        factor = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]

        for i in range(2):
            self.qtgui_number_sink_0.set_min(i, -60)
            self.qtgui_number_sink_0.set_max(i, 0)
            self.qtgui_number_sink_0.set_color(i, colors[i][0], colors[i][1])
            if len(labels[i]) == 0:
                self.qtgui_number_sink_0.set_label(i, "Data {0}".format(i))
            else:
                self.qtgui_number_sink_0.set_label(i, labels[i])
            self.qtgui_number_sink_0.set_unit(i, units[i])
            self.qtgui_number_sink_0.set_factor(i, factor[i])

        self.qtgui_number_sink_0.enable_autoscale(False)
        self._qtgui_number_sink_0_win = sip.wrapinstance(self.qtgui_number_sink_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_number_sink_0_win)
        self.qtgui_freq_sink_x_1 = qtgui.freq_sink_c(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            "Digital Sidebands", #name
            3,
            None # parent
        )
        self.qtgui_freq_sink_x_1.set_update_time(0.10)
        self.qtgui_freq_sink_x_1.set_y_axis((-140), 10)
        self.qtgui_freq_sink_x_1.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_x_1.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_x_1.enable_autoscale(False)
        self.qtgui_freq_sink_x_1.enable_grid(False)
        self.qtgui_freq_sink_x_1.set_fft_average(0.05)
        self.qtgui_freq_sink_x_1.enable_axis_labels(True)
        self.qtgui_freq_sink_x_1.enable_control_panel(False)
        self.qtgui_freq_sink_x_1.set_fft_window_normalized(False)



        labels = ['Lower Sideband', 'Upper Sideband', 'Analog FM', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(3):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_x_1.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_x_1.set_line_label(i, labels[i])
            self.qtgui_freq_sink_x_1.set_line_width(i, widths[i])
            self.qtgui_freq_sink_x_1.set_line_color(i, colors[i])
            self.qtgui_freq_sink_x_1.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_x_1_win = sip.wrapinstance(self.qtgui_freq_sink_x_1.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_freq_sink_x_1_win)
        self.qtgui_freq_sink_x_0 = qtgui.freq_sink_c(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            "Full Spectrum", #name
            1,
            None # parent
        )
        self.qtgui_freq_sink_x_0.set_update_time(0.10)
        self.qtgui_freq_sink_x_0.set_y_axis((-140), 10)
        self.qtgui_freq_sink_x_0.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_x_0.enable_autoscale(False)
        self.qtgui_freq_sink_x_0.enable_grid(False)
        self.qtgui_freq_sink_x_0.set_fft_average(1.0)
        self.qtgui_freq_sink_x_0.enable_axis_labels(True)
        self.qtgui_freq_sink_x_0.enable_control_panel(False)
        self.qtgui_freq_sink_x_0.set_fft_window_normalized(False)

        self.qtgui_freq_sink_x_0.disable_legend()


        labels = ['Full Spectrum', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_freq_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_freq_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_freq_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_x_0_win = sip.wrapinstance(self.qtgui_freq_sink_x_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_freq_sink_x_0_win)
        self.osmosdr_source_0 = osmosdr.source(
            args="numchan=" + str(1) + " " + ''
        )
        self.osmosdr_source_0.set_time_now(osmosdr.time_spec_t(time.time()), osmosdr.ALL_MBOARDS)
        self.osmosdr_source_0.set_sample_rate(samp_rate)
        self.osmosdr_source_0.set_center_freq(freq, 0)
        self.osmosdr_source_0.set_freq_corr(0, 0)
        self.osmosdr_source_0.set_dc_offset_mode(0, 0)
        self.osmosdr_source_0.set_iq_balance_mode(0, 0)
        self.osmosdr_source_0.set_gain_mode(False, 0)
        self.osmosdr_source_0.set_gain(40, 0)
        self.osmosdr_source_0.set_if_gain(20, 0)
        self.osmosdr_source_0.set_bb_gain(20, 0)
        self.osmosdr_source_0.set_antenna('', 0)
        self.osmosdr_source_0.set_bandwidth(0, 0)
        self.low_pass_filter_0_0 = filter.fir_filter_ccf(
            1,
            firdes.low_pass(
                1,
                samp_rate,
                90e3,
                10e3,
                window.WIN_BLACKMAN,
                6.76))
        self._freq_display_tool_bar = Qt.QToolBar(self)

        if None:
            self._freq_display_formatter = None
        else:
            self._freq_display_formatter = lambda x: eng_notation.num_to_str(x)

        self._freq_display_tool_bar.addWidget(Qt.QLabel("Frequency (MHz)"))
        self._freq_display_label = Qt.QLabel(str(self._freq_display_formatter(self.freq_display)))
        self._freq_display_tool_bar.addWidget(self._freq_display_label)
        self.top_grid_layout.addWidget(self._freq_display_tool_bar, 2, 0, 1, 2)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.ejfat_e2sar_segmenter_sink_0 = ejfat.e2sar_segmenter_sink(uri=ejfat_uri, data_id=data_id, event_src_id=event_src_id, vector_size=vlen, use_cp=False, mtu=9000, rate_gbps=1.0)
        def _digital_indicator_probe():
          self.flowgraph_started.wait()
          while True:

            val = self.blocks_probe_signal_0.level()
            try:
              try:
                self.doc.add_next_tick_callback(functools.partial(self.set_digital_indicator,val))
              except AttributeError:
                self.set_digital_indicator(val)
            except AttributeError:
              pass
            time.sleep(1.0 / (10))
        _digital_indicator_thread = threading.Thread(target=_digital_indicator_probe)
        _digital_indicator_thread.daemon = True
        _digital_indicator_thread.start()
        self.blocks_threshold_ff_1 = blocks.threshold_ff(digital_threshold, digital_threshold, 0)
        self.blocks_threshold_ff_0 = blocks.threshold_ff(digital_threshold, digital_threshold, 0)
        self.blocks_stream_to_vector_0 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, vlen)
        self.blocks_nlog10_ff_2 = blocks.nlog10_ff(10, 1, 0)
        self.blocks_nlog10_ff_1 = blocks.nlog10_ff(10, 1, 0)
        self.blocks_nlog10_ff_0 = blocks.nlog10_ff(10, 1, 0)
        self.blocks_moving_average_2 = blocks.moving_average_ff(energy_avg_len, (1.0/energy_avg_len), 4000, 1)
        self.blocks_moving_average_1 = blocks.moving_average_ff(energy_avg_len, (1.0/energy_avg_len), 4000, 1)
        self.blocks_moving_average_0 = blocks.moving_average_ff(energy_avg_len, (1.0/energy_avg_len), 4000, 1)
        self.blocks_max_xx_0 = blocks.max_ff(1, 1)
        self.blocks_divide_xx_1 = blocks.divide_ff(1)
        self.blocks_divide_xx_0 = blocks.divide_ff(1)
        self.blocks_complex_to_mag_squared_2 = blocks.complex_to_mag_squared(1)
        self.blocks_complex_to_mag_squared_1 = blocks.complex_to_mag_squared(1)
        self.blocks_complex_to_mag_squared_0 = blocks.complex_to_mag_squared(1)
        self.band_pass_filter_upper = filter.fir_filter_ccc(
            1,
            firdes.complex_band_pass(
                1,
                samp_rate,
                (upper_sideband_center - sideband_bw/2),
                (upper_sideband_center + sideband_bw/2),
                5000,
                window.WIN_HAMMING,
                6.76))
        self.band_pass_filter_lower = filter.fir_filter_ccc(
            1,
            firdes.complex_band_pass(
                1,
                samp_rate,
                (lower_sideband_center - sideband_bw/2),
                (lower_sideband_center + sideband_bw/2),
                5000,
                window.WIN_HAMMING,
                6.76))


        ##################################################
        # Connections
        ##################################################
        self.connect((self.band_pass_filter_lower, 0), (self.blocks_complex_to_mag_squared_0, 0))
        self.connect((self.band_pass_filter_lower, 0), (self.qtgui_freq_sink_x_1, 0))
        self.connect((self.band_pass_filter_upper, 0), (self.blocks_complex_to_mag_squared_1, 0))
        self.connect((self.band_pass_filter_upper, 0), (self.qtgui_freq_sink_x_1, 1))
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.blocks_moving_average_0, 0))
        self.connect((self.blocks_complex_to_mag_squared_1, 0), (self.blocks_moving_average_1, 0))
        self.connect((self.blocks_complex_to_mag_squared_2, 0), (self.blocks_moving_average_2, 0))
        self.connect((self.blocks_divide_xx_0, 0), (self.blocks_nlog10_ff_0, 0))
        self.connect((self.blocks_divide_xx_1, 0), (self.blocks_nlog10_ff_1, 0))
        self.connect((self.blocks_max_xx_0, 0), (self.blocks_probe_signal_0, 0))
        self.connect((self.blocks_max_xx_0, 0), (self.qtgui_number_sink_1, 0))
        self.connect((self.blocks_moving_average_0, 0), (self.blocks_divide_xx_0, 0))
        self.connect((self.blocks_moving_average_1, 0), (self.blocks_divide_xx_1, 0))
        self.connect((self.blocks_moving_average_2, 0), (self.blocks_divide_xx_0, 1))
        self.connect((self.blocks_moving_average_2, 0), (self.blocks_divide_xx_1, 1))
        self.connect((self.blocks_moving_average_2, 0), (self.blocks_nlog10_ff_2, 0))
        self.connect((self.blocks_nlog10_ff_0, 0), (self.blocks_threshold_ff_0, 0))
        self.connect((self.blocks_nlog10_ff_0, 0), (self.qtgui_number_sink_0, 0))
        self.connect((self.blocks_nlog10_ff_1, 0), (self.blocks_threshold_ff_1, 0))
        self.connect((self.blocks_nlog10_ff_1, 0), (self.qtgui_number_sink_0, 1))
        self.connect((self.blocks_nlog10_ff_2, 0), (self.blocks_probe_signal_1, 0))
        self.connect((self.blocks_nlog10_ff_2, 0), (self.qtgui_number_sink_2, 0))
        self.connect((self.blocks_stream_to_vector_0, 0), (self.ejfat_e2sar_segmenter_sink_0, 0))
        self.connect((self.blocks_threshold_ff_0, 0), (self.blocks_max_xx_0, 0))
        self.connect((self.blocks_threshold_ff_1, 0), (self.blocks_max_xx_0, 1))
        self.connect((self.low_pass_filter_0_0, 0), (self.blocks_complex_to_mag_squared_2, 0))
        self.connect((self.low_pass_filter_0_0, 0), (self.blocks_stream_to_vector_0, 0))
        self.connect((self.low_pass_filter_0_0, 0), (self.qtgui_freq_sink_x_1, 2))
        self.connect((self.osmosdr_source_0, 0), (self.band_pass_filter_lower, 0))
        self.connect((self.osmosdr_source_0, 0), (self.band_pass_filter_upper, 0))
        self.connect((self.osmosdr_source_0, 0), (self.low_pass_filter_0_0, 0))
        self.connect((self.osmosdr_source_0, 0), (self.qtgui_freq_sink_x_0, 0))
        self.connect((self.osmosdr_source_0, 0), (self.qtgui_waterfall_sink_x_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "fm_digital_detector_e2sar")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.osmosdr_source_0.set_center_freq(self.freq, 0)
        self.set_freq_display((self.freq/1e6))

    def get_vlen(self):
        return self.vlen

    def set_vlen(self, vlen):
        self.vlen = vlen

    def get_upper_sideband_center(self):
        return self.upper_sideband_center

    def set_upper_sideband_center(self, upper_sideband_center):
        self.upper_sideband_center = upper_sideband_center
        self.band_pass_filter_upper.set_taps(firdes.complex_band_pass(1, self.samp_rate, (self.upper_sideband_center - self.sideband_bw/2), (self.upper_sideband_center + self.sideband_bw/2), 5000, window.WIN_HAMMING, 6.76))

    def get_signal_level(self):
        return self.signal_level

    def set_signal_level(self, signal_level):
        self.signal_level = signal_level

    def get_sideband_bw(self):
        return self.sideband_bw

    def set_sideband_bw(self, sideband_bw):
        self.sideband_bw = sideband_bw
        self.band_pass_filter_lower.set_taps(firdes.complex_band_pass(1, self.samp_rate, (self.lower_sideband_center - self.sideband_bw/2), (self.lower_sideband_center + self.sideband_bw/2), 5000, window.WIN_HAMMING, 6.76))
        self.band_pass_filter_upper.set_taps(firdes.complex_band_pass(1, self.samp_rate, (self.upper_sideband_center - self.sideband_bw/2), (self.upper_sideband_center + self.sideband_bw/2), 5000, window.WIN_HAMMING, 6.76))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.band_pass_filter_lower.set_taps(firdes.complex_band_pass(1, self.samp_rate, (self.lower_sideband_center - self.sideband_bw/2), (self.lower_sideband_center + self.sideband_bw/2), 5000, window.WIN_HAMMING, 6.76))
        self.band_pass_filter_upper.set_taps(firdes.complex_band_pass(1, self.samp_rate, (self.upper_sideband_center - self.sideband_bw/2), (self.upper_sideband_center + self.sideband_bw/2), 5000, window.WIN_HAMMING, 6.76))
        self.low_pass_filter_0_0.set_taps(firdes.low_pass(1, self.samp_rate, 90e3, 10e3, window.WIN_BLACKMAN, 6.76))
        self.osmosdr_source_0.set_sample_rate(self.samp_rate)
        self.qtgui_freq_sink_x_0.set_frequency_range(0, self.samp_rate)
        self.qtgui_freq_sink_x_1.set_frequency_range(0, self.samp_rate)
        self.qtgui_waterfall_sink_x_0.set_frequency_range(0, self.samp_rate)

    def get_lower_sideband_center(self):
        return self.lower_sideband_center

    def set_lower_sideband_center(self, lower_sideband_center):
        self.lower_sideband_center = lower_sideband_center
        self.band_pass_filter_lower.set_taps(firdes.complex_band_pass(1, self.samp_rate, (self.lower_sideband_center - self.sideband_bw/2), (self.lower_sideband_center + self.sideband_bw/2), 5000, window.WIN_HAMMING, 6.76))

    def get_freq_display(self):
        return self.freq_display

    def set_freq_display(self, freq_display):
        self.freq_display = freq_display
        Qt.QMetaObject.invokeMethod(self._freq_display_label, "setText", Qt.Q_ARG("QString", str(self._freq_display_formatter(self.freq_display))))

    def get_event_src_id(self):
        return self.event_src_id

    def set_event_src_id(self, event_src_id):
        self.event_src_id = event_src_id

    def get_energy_avg_len(self):
        return self.energy_avg_len

    def set_energy_avg_len(self, energy_avg_len):
        self.energy_avg_len = energy_avg_len
        self.blocks_moving_average_0.set_length_and_scale(self.energy_avg_len, (1.0/self.energy_avg_len))
        self.blocks_moving_average_1.set_length_and_scale(self.energy_avg_len, (1.0/self.energy_avg_len))
        self.blocks_moving_average_2.set_length_and_scale(self.energy_avg_len, (1.0/self.energy_avg_len))

    def get_ejfat_uri(self):
        return self.ejfat_uri

    def set_ejfat_uri(self, ejfat_uri):
        self.ejfat_uri = ejfat_uri

    def get_digital_threshold(self):
        return self.digital_threshold

    def set_digital_threshold(self, digital_threshold):
        self.digital_threshold = digital_threshold
        self.blocks_threshold_ff_0.set_hi(self.digital_threshold)
        self.blocks_threshold_ff_0.set_lo(self.digital_threshold)
        self.blocks_threshold_ff_1.set_hi(self.digital_threshold)
        self.blocks_threshold_ff_1.set_lo(self.digital_threshold)

    def get_digital_indicator(self):
        return self.digital_indicator

    def set_digital_indicator(self, digital_indicator):
        self.digital_indicator = digital_indicator

    def get_data_id(self):
        return self.data_id

    def set_data_id(self, data_id):
        self.data_id = data_id




def main(top_block_cls=fm_digital_detector_e2sar, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()
    tb.flowgraph_started.set()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
