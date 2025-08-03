#!/usr/bin/env python3

import h5py
import json
import numpy
import zmq
import time
from pathlib import Path

ccd_pub_address = os.environ.get("ZMQ_PUB_ADDRESS")
filename = os.environ.get("FILENAME")

def send_one_image(sock, filename, inter_event_delay):
  f = h5py.File(filename, 'r')

  entry0 = f['/entry0']
  metadata = json.loads(f['/metadata'][()])

  ccd0 = entry0['ccd0']
  dark = ccd0['dark']
  exp = ccd0['exp']
  ######

  events = []
  start_event = {'event':'start', 'metadata' : metadata }
  stop_event = {'event':'stop', 'data' : None }

  dark_items = [int(x) for x in list(dark)]
  exp_items = [int(x) for x in list(exp)]

  dark_items.sort()
  exp_items.sort()


  ###################
  for d in dark_items:
    frame_event = {}
    frame_event['ccd_mode'] = 'dark'
    frame_event['dwell'] = metadata['dwell1']
    frame_event['ccd_frame'] = numpy.array(dark[str(d)])

    frame_event = { 'event' : 'frame', 'data' : frame_event}
    events.append(frame_event)

  for e in exp_items:
    frame_event = {}
    frame_event['ccd_mode'] = 'exp'
    frame_event['index'] = e
    frame_event['dwell'] = metadata['dwell1']
    frame_event['xPos'] = metadata['translations'][e][1] 
    frame_event['yPos'] = metadata['translations'][e][0]
    frame_event['ccd_frame'] = numpy.array(exp[str(e)])
    frame_event = { 'event' : 'frame', 'data' : frame_event}
    events.append(frame_event)

  t0 = time.time()
  sock.send_pyobj(start_event)
  for i, event in enumerate(events):
      print("sending event: ", event["event"], i)
      sock.send_pyobj(event)
      time.sleep(inter_event_delay)
  sock.send_pyobj(stop_event)
  print("Time per event: %2f" %((time.time()-t0)/len(events)))

def main():
  ctx = zmq.Context()
  sock = ctx.socket(zmq.PUB)
  sock.bind(ccd_pub_address)

  time.sleep(2)

  while True:
    try:
        if not Path(filename).exists:
            print(f'Skipping nonexistent file {filename}')
            continue
        send_one_image(sock, filename, 0.02)
        time.sleep(5)
    except Exception as e:
          print("Skipping ", str(e))

  sock.close()

if __name__ == '__main__':
  main()

