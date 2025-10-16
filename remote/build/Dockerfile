FROM ibaldin/e2sar:0.2.2a2

RUN apt update && apt -y install iproute2 dnsutils iputils-ping netcat-traditional traceroute git

RUN mkdir -p /opt/
RUN cd /opt && git clone https://github.com/esnet/ejfat_demos/
COPY ejfat.sh /usr/local/bin/ejfat
RUN chmod +x /usr/local/bin/ejfat
