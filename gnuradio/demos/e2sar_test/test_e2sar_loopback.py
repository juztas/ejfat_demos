#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: E2SAR Loopback Test
# Description: E2SAR Segmenter and Reassembler Test
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import analog
from gnuradio import blocks
from gnuradio import ejfat
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import sip
import threading



class test_e2sar_loopback(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "E2SAR Loopback Test", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("E2SAR Loopback Test")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "test_e2sar_loopback")

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
        self.data_port = data_port = 10000
        self.data_ip = data_ip = "127.0.0.1"
        self.vector_size = vector_size = 1024
        self.signal_freq = signal_freq = 100
        self.samp_rate = samp_rate = 1000000
        self.ejfat_uri = ejfat_uri = "ejfat://token@127.0.0.1:18020/lb/36?data=" + data_ip + ":" + str(data_port)

        ##################################################
        # Blocks
        ##################################################

        self.qtgui_time_sink_x_0 = qtgui.time_sink_f(
            8192, #size
            samp_rate, #samp_rate
            "Received Signal", #name
            4, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_0.set_update_time(0.10)
        self.qtgui_time_sink_x_0.set_y_axis(-1.5, 1.5)

        self.qtgui_time_sink_x_0.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_0.enable_tags(True)
        self.qtgui_time_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_AUTO, qtgui.TRIG_SLOPE_POS, 0, 0, 0, "")
        self.qtgui_time_sink_x_0.enable_autoscale(True)
        self.qtgui_time_sink_x_0.enable_grid(True)
        self.qtgui_time_sink_x_0.enable_axis_labels(True)
        self.qtgui_time_sink_x_0.enable_control_panel(False)
        self.qtgui_time_sink_x_0.enable_stem_plot(False)


        labels = ['Transmit I', 'Transmit Q', 'Receive I', 'Receive Q', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'green', 'magenta', 'red', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(4):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_0_win = sip.wrapinstance(self.qtgui_time_sink_x_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_time_sink_x_0_win)
        self.qtgui_freq_sink_x_0 = qtgui.freq_sink_c(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            "Received Spectrum", #name
            2,
            None # parent
        )
        self.qtgui_freq_sink_x_0.set_update_time(0.10)
        self.qtgui_freq_sink_x_0.set_y_axis((-140), 10)
        self.qtgui_freq_sink_x_0.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_x_0.enable_autoscale(True)
        self.qtgui_freq_sink_x_0.enable_grid(True)
        self.qtgui_freq_sink_x_0.set_fft_average(1.0)
        self.qtgui_freq_sink_x_0.enable_axis_labels(True)
        self.qtgui_freq_sink_x_0.enable_control_panel(False)
        self.qtgui_freq_sink_x_0.set_fft_window_normalized(False)



        labels = ['Received', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(2):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_freq_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_freq_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_freq_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_x_0_win = sip.wrapinstance(self.qtgui_freq_sink_x_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_freq_sink_x_0_win)
        self.ejfat_e2sar_segmenter_sink_0 = ejfat.e2sar_segmenter_sink(uri=ejfat_uri, data_id=1285, event_src_id=287454020, vector_size=vector_size, use_cp=False, mtu=9000, rate_gbps=1.0)
        self.ejfat_e2sar_reassembler_source_0 = ejfat.e2sar_reassembler_source(
            uri=ejfat_uri,
            data_ip=data_ip,
            starting_port=data_port,
            vector_size=vector_size,
            num_recv_threads=1,
            use_cp=False,
            use_host_address=False,
            period_ms=100,
            validate_cert=True,
            with_lb_header=True,
            event_timeout_ms=5000,
            rcv_socket_buf_size=3145728,
            port_range=(-1),
            epoch_ms=1000,
            ki=0.0,
            kp=0.0,
            kd=0.0,
            set_point=0.0,
            weight=1.0,
            min_factor=0.5,
            max_factor=2.0
        )
        self.blocks_vector_to_stream_0 = blocks.vector_to_stream(gr.sizeof_gr_complex*1, vector_size)
        self.blocks_throttle2_0 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_stream_to_vector_0 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, vector_size)
        self.blocks_complex_to_float_0_0 = blocks.complex_to_float(1)
        self.blocks_complex_to_float_0 = blocks.complex_to_float(1)
        self.analog_sig_source_x_0 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, signal_freq, 0.5, 0.5, 0)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_throttle2_0, 0))
        self.connect((self.blocks_complex_to_float_0, 1), (self.qtgui_time_sink_x_0, 1))
        self.connect((self.blocks_complex_to_float_0, 0), (self.qtgui_time_sink_x_0, 0))
        self.connect((self.blocks_complex_to_float_0_0, 1), (self.qtgui_time_sink_x_0, 3))
        self.connect((self.blocks_complex_to_float_0_0, 0), (self.qtgui_time_sink_x_0, 2))
        self.connect((self.blocks_stream_to_vector_0, 0), (self.ejfat_e2sar_segmenter_sink_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.blocks_complex_to_float_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.blocks_stream_to_vector_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.qtgui_freq_sink_x_0, 1))
        self.connect((self.blocks_vector_to_stream_0, 0), (self.blocks_complex_to_float_0_0, 0))
        self.connect((self.blocks_vector_to_stream_0, 0), (self.qtgui_freq_sink_x_0, 0))
        self.connect((self.ejfat_e2sar_reassembler_source_0, 0), (self.blocks_vector_to_stream_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "test_e2sar_loopback")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_data_port(self):
        return self.data_port

    def set_data_port(self, data_port):
        self.data_port = data_port
        self.set_ejfat_uri("ejfat://token@127.0.0.1:18020/lb/36?data=" + self.data_ip + ":" + str(self.data_port))

    def get_data_ip(self):
        return self.data_ip

    def set_data_ip(self, data_ip):
        self.data_ip = data_ip
        self.set_ejfat_uri("ejfat://token@127.0.0.1:18020/lb/36?data=" + self.data_ip + ":" + str(self.data_port))

    def get_vector_size(self):
        return self.vector_size

    def set_vector_size(self, vector_size):
        self.vector_size = vector_size

    def get_signal_freq(self):
        return self.signal_freq

    def set_signal_freq(self, signal_freq):
        self.signal_freq = signal_freq
        self.analog_sig_source_x_0.set_frequency(self.signal_freq)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.analog_sig_source_x_0.set_sampling_freq(self.samp_rate)
        self.blocks_throttle2_0.set_sample_rate(self.samp_rate)
        self.qtgui_freq_sink_x_0.set_frequency_range(0, self.samp_rate)
        self.qtgui_time_sink_x_0.set_samp_rate(self.samp_rate)

    def get_ejfat_uri(self):
        return self.ejfat_uri

    def set_ejfat_uri(self, ejfat_uri):
        self.ejfat_uri = ejfat_uri




def main(top_block_cls=test_e2sar_loopback, options=None):

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
