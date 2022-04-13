# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: lvm_actors.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import asyncio
import sys
import uuid

from logging import DEBUG

from sdsstools.logger import StreamFormatter  
from sdsstools import get_logger, read_yaml_file
from sdsstools.logger import SDSSLogger

from clu import AMQPClient, CommandStatus

from cluplus.proxy import Proxy, invoke, unpack

lvm_amqpc = AMQPClient(name=f"{sys.argv[0]}.proxy-{uuid.uuid4().hex[:8]}")
logger = lvm_amqpc.log

class lvm:
    def execute(coro, verbose=None):
        async def start(coro):
            await coro.start()

        if verbose:
           logger.sh.setLevel(DEBUG)
           #logger.sh.formatter = StreamFormatter(fmt='%(asctime)s %(name)s %(levelname)s %(filename)s:%(lineno)d: \033[1m%(message)s\033[21m') 
        return lvm_amqpc.loop.run_until_complete(coro)

    class sci:
        foc = Proxy(lvm_amqpc, "lvm.sci.foc")
        km = Proxy(lvm_amqpc, "lvm.sci.km")
        pwi = Proxy(lvm_amqpc, "lvm.sci.pwi")
        agc = Proxy(lvm_amqpc, "lvm.sci.agcam")
        ag = Proxy(lvm_amqpc, "lvm.sci.ag")

        async def start():
            await lvm_amqpc.start()
            rc = await asyncio.gather(
                lvm.sci.foc.start(),
                lvm.sci.km.start(),
                lvm.sci.pwi.start(),
                lvm.sci.agc.start(),
                lvm.sci.ag.start(),
                return_exceptions=True
            )
            logger.debug(str(rc))
            return lvm.sci


    class skye:
        foc = Proxy(lvm_amqpc, "lvm.skye.foc")
        km = Proxy(lvm_amqpc, "lvm.skye.km")
        pwi = Proxy(lvm_amqpc, "lvm.skye.pwi")
        agc = Proxy(lvm_amqpc, "lvm.skye.agcam")
        ag = Proxy(lvm_amqpc, "lvm.skye.ag")
        
        async def start():
            await lvm_amqpc.start()
            await invoke(
                lvm.skye.foc.start(),
                lvm.skye.km.start(),
                lvm.skye.pwi.start(),
                lvm.skye.agc.start(),
                lvm.skye.ag.start(),
                return_exceptions=True
            )
            logger.debug(str(rc))
            return lvm.skye


    class skyw:
        foc = Proxy(lvm_amqpc, "lvm.skyw.foc")
        km = Proxy(lvm_amqpc, "lvm.skyw.km")
        pwi = Proxy(lvm_amqpc, "lvm.skyw.pwi")
        agc = Proxy(lvm_amqpc, "lvm.skyw.agcam")
        ag = Proxy(lvm_amqpc, "lvm.skyw.ag")
        async def start():
            await lvm_amqpc.start()
            await invoke(
                lvm.skyw.foc.start(),
                lvm.skyw.km.start(),
                lvm.skyw.pwi.start(),
                lvm.skyw.agc.start(),
                lvm.skyw.ag.start(),
                return_exceptions=True
            )
            logger.debug(str(rc))
            return lvm.skyw


    class spec:
        foc = Proxy(lvm_amqpc, "lvm.spec.foc")
        fibsel = Proxy(lvm_amqpc, "lvm.spec.fibsel")
        pwi = Proxy(lvm_amqpc, "lvm.spec.pwi")
        agc = Proxy(lvm_amqpc, "lvm.spec.agcam")
        ag = Proxy(lvm_amqpc, "lvm.spec.ag")
        async def start():
            await lvm_amqpc.start()
            await invoke(
                lvm.spec.foc.start(),
                lvm.spec.fibsel.start(),
                lvm.spec.pwi.start(),
                lvm.spec.agc.start(),
                lvm.spec.ag.start(),
                return_exceptions=True
            )
            logger.debug(str(rc))
            return lvm.spec

    def from_string(subsys: str, amqpc = None):
        if amqpc:
            lvm_amqpc = amqpc
            logger = lvm_amqpc.log
        if subsys == 'sci': 
            return lvm.sci.start()
        elif subsys == 'skye': 
            return lvm.skye.sci.start()
        elif subsys == 'skyw': 
            return lvm.skyw.sci.start()
        elif subsys == 'spec': 
            return lvm.spec.sci.start()
        else: return None


