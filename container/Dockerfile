FROM python:3.10-slim-bullseye

## Get some karma ##
MAINTAINER Florian Briegel, briegel@mpia.de

# RUN apt update -y
# RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get -y install tzdata
# RUN apt install -y sudo git lsof pkg-config
# RUN apt install -y python3-pip

# RUN pip3 install sdss-lvmtipo sdss-cluplus numpy scipy sep expandvars

WORKDIR /root

COPY . lvmagp
RUN cd lvmagp && pip install .

CMD ["/root/lvmagp/container/run-actor.sh"]
