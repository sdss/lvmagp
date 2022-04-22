# lvmagp

[![Versions](https://img.shields.io/badge/python->3.7-blue)](https://img.shields.io/badge/python->3.7-blue)
[![Documentation Status](https://readthedocs.org/projects/sdss-lvmagp/badge/?version=latest)](https://sdss-lvmagp.readthedocs.io/en/latest/?badge=latest)
[![Travis (.org)](https://img.shields.io/travis/sdss/lvmagp)](https://travis-ci.org/sdss/lvmagp)
[![codecov](https://codecov.io/gh/sdss/lvmagp/branch/main/graph/badge.svg)](https://codecov.io/gh/sdss/lvmagp)

lvmagp which controls focuser, guide camera and mount. 

# Quickstart
## Install
    git clone --recurse-submodules -j8 --remote-submodules https://github.com/sdss/lvm.git
    cd lvm
    (cd lvmcam && git switch refactor && poetry update && poetry install)
    (cd lvmagp && git switch refactor && poetry update && poetry install)

# Run actors

    (cd lvmtan && poetry run container_start --kill --name lvm.all)
    (cd lvmpwi && poetry run container_start --simulator --name=lvm.sci.pwi&)

    (cd lvmcam && poetry run lvmcam -c python/lvmcam/etc/lvm.sci.agcam.yml start --debug &)
    (cd lvmcam && poetry run python utils/simple_camui.py &)

    (cd lvmagp && poetry run lvmagp -c python/lvmagp/etc/lvm.sci.agp.yml start --debug &)

# Run example scripts - maybe in a extra shell
    cd lvmagp 

    poetry run python python/lvm/tel/aquisition.py --help

    poetry run python python/lvm/tel/aquisition.py -r 22 -d -46 -v 

    poetry run python python/lvm/tel/focus.py -f -v

    poetry run python python/lvm/tel/calibrate.py -o 20 -v

## Guider start/stop from python shell
Do not use this in a python script without try/except.

    import sys
    import uuid
    from logging import DEBUG
    from clu import AMQPClient, CommandStatus
    from cluplus.proxy import Proxy, invoke, unpack
    
    amqpc = AMQPClient(name=f"{sys.argv[0]}.client-{uuid.uuid4().hex[:8]}")
    ag = Proxy(amqpc, "lvm.sci.ag").start()
    ag.guideStart()
    ag.status()
    ag.guideStop()

