# the docker image for project
FROM python:3

WORKDIR /usr/src/app

# install darknet
RUN \
	apt-get update && apt-get install -y \
	autoconf \
        automake \
	libtool \
	build-essential \
	git

# addons
RUN \
	apt-get install -y \
	wget

# build repo
RUN \
	git clone https://github.com/pjreddie/darknet && \
	cd darknet && \
	make

RUN mkdir dutch_traffic_monitor
COPY ./dutch_traffic_monitor/ ./dutch_traffic_monitor
COPY requirements.txt ./


ENV MYSQL_HOST mysql
ENV MYSQL_PORT 3306
ENV MYSQL_USER_NAME root
ENV MYSQL_PASSWORD mysqladmin

RUN pip install -r requirements.txt

COPY ./run.sh .