ARG PYTHON_VERSION=3.11
# FROM python:${PYTHON_VERSION}-slim AS base
FROM ibaldin/e2sar:0.2.1a3

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt update && apt install -y git vim

WORKDIR /app

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

#RUN git clone https://github.com/allevitan/ACME_Data_Cleaning_And_Assembly
#RUN python3 -m pip install -e ./ACME_Data_Cleaning_And_Assembly

########
#######

#COPY requirements.txt preprocess.py reconstruct.py display.py main.py /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY src /app
ENV PYTHONPATH=/app

# RUN git clone https://github.com/cdtools-developers/cdtools # using pip install cdtools-py


#RUN python3 main.py


