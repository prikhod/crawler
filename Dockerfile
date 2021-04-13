FROM ubuntu:focal
ENV TZ=Europe/London
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt -yqq update \
    && apt -yqq install \
    wget \
    gnupg

RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb https://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

RUN apt -yqq update \
    && apt -yqq install \
    python3.8 \
    python3-pip \
    tzdata \
    google-chrome-stable

COPY . /usr/src/crawler
WORKDIR /usr/src/crawler

RUN pip3 install pip --no-cache-dir -r requirements.txt \
    && python3 setup.py install
