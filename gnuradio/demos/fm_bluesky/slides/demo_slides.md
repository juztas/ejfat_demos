---
marp: true
theme: default
paginate: true
style: |
  section {
    background-color: #FAFAFA;
    font-family: 'Inter', 'Roboto', sans-serif;
  }
  h1 {
    color: #6B7D4F;
    font-weight: bold;
  }
  h2 {
    color: #1A1A1A;
    font-weight: 600;
  }
---

# FM Radio E2SAR Demo
## Welcome

This interactive demo will guide you through:
- Reserving an EJFAT load balancer
- Transmitting FM radio signals via E2SAR
- Receiving and decoding the signal

**Duration:** ~5-10 minutes
**Prerequisites:** GNU Radio, E2SAR, RTL-SDR (or simulated source)

---

# Step 1: Reserve Load Balancer
## Action Required ⚡

**What to do:**
1. Review the Admin URI in the control panel
2. Click the **"Reserve LB"** button

**What's happening:**
- Contacts EJFAT admin server at the specified URI
- Allocates a dedicated load balancer instance
- Returns an Instance URI for your data transmission session

**Next:** Once reserved, the Instance URI field will automatically populate.

---

# Step 2: Start Transmitter
## Action Required ⚡

**What to do:**
Click the **"Start TX"** button in the Transmitter panel

**What's happening:**
- Launches `fm_transmitter_e2sar.py` GNU Radio flowgraph
- Initializes RTL-SDR (or signal source)
- Connects to E2SAR segmenter with your Instance URI
- Begins capturing FM signals at 98.5 MHz (default)

**Next:** Wait for "Status: Running" indicator

---

# Step 3: Start Receiver
## Action Required ⚡

**What to do:**
Click the **"Start RX"** button in the Receiver panel

**What's happening:**
- Launches `fm_receiver_e2sar.py` GNU Radio flowgraph
- Initializes E2SAR reassembler to receive data
- Connects to your load balancer instance
- Begins FM demodulation and audio playback

**Next:** You should hear audio from the FM station!

---

# Step 4: Demo Running
## What You're Seeing 🎉

**Signal Flow:**
```
RTL-SDR → GNU Radio TX → E2SAR Segmenter →
EJFAT Load Balancer → E2SAR Reassembler →
GNU Radio RX → Audio Output
```

**Key Concepts:**
- **E2SAR Segmenter:** Breaks GNU Radio data into EJFAT packets
- **Load Balancer:** Routes packets to receiver(s)
- **E2SAR Reassembler:** Reconstructs original signal

**Try:** Change the frequency in the Transmitter GUI to tune to different FM stations!

---

# Step 5: Monitor Status
## Observing the System 📊

**Check the Status Panel:**
- LB Status: Should show "Reserved"
- TX Process: Should show "Running"
- RX Process: Should show "Running"
- Demo Step: 5/7

**System Logs:**
Expand the logs panel to see:
- Process startup messages
- E2SAR connection status
- Packet transmission statistics

**Next:** Experiment with the demo, then proceed to cleanup

---

# Step 6: Cleanup
## Action Required ⚡

**What to do:**
1. Click **"Stop RX"** to stop the receiver
2. Click **"Stop TX"** to stop the transmitter
3. Click **"Free LB"** to release the load balancer

**What's happening:**
- Gracefully shuts down GNU Radio flowgraphs
- Stops E2SAR segmenter/reassembler
- Releases load balancer resources

**Next:** Review what you learned!

---

# Conclusion
## Summary 🎓

**What you accomplished:**
✅ Reserved an EJFAT load balancer
✅ Transmitted FM radio via E2SAR data plane
✅ Received and decoded the signal
✅ Experienced real-time network load balancing

**Key Takeaways:**
- E2SAR enables efficient data streaming over EJFAT
- Load balancers provide scalable, fault-tolerant routing
- GNU Radio integrates seamlessly with E2SAR blocks

**Thank you for trying the FM Radio E2SAR Demo!**

---
