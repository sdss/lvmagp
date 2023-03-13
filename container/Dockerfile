FROM ubuntu:20.04

## Get some karma ##
MAINTAINER Florian Briegel, briegel@mpia.de

# podman  build --tag ubuntu_lvmt_agp --rm .

# podman run -ti --rm --name lvmt_agp -v .:/root/lvmt:Z -P localhost/ubuntu_lvmt_agp

RUN apt update -y && \
    apt install -y wget && \
    echo "8\n7\n" | apt install -y software-properties-common && \
    echo "30\n1\n" | apt install -y keyboard-configuration && \
    wget -qO - https://svn.mpia.de/repo/linux/ubuntu/archive.key | apt-key add - && \
    echo "deb https://svn.mpia.de/repo/linux/ubuntu focal main" > /etc/apt/sources.list.d/mpia.list

RUN apt update -y

RUN apt install -y sudo git lsof pkg-config
RUN apt install -y python3-pip
RUN pip3 install sdss-lvmtipo sdss-cluplus numpy scipy sep expandvars

COPY . lvmagp
RUN cd lvmagp && pip install .

WORKDIR /root

#COPY run-agp.sh /root

CMD ["/root/lvmagp/container/run-actor.sh"]
