
import asyncio

from cluplus.proxy import invoke
from lvmtipo.actors import lvm

from lvmagp.images import Image
from lvmagp.images.processors.detection import DaophotSourceDetection, SepSourceDetection
from lvmagp.images.processors.astrometry import AstrometryDotNet
from lvmagp.focus.focusseries import PhotometryFocusSeries, ProjectionFocusSeries

import logging

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

await lvm.sci.start()

await invoke(lvm.sci.foc.status(), lvm.sci.km.status(), lvm.sci.pwi.status())

dsd = DaophotSourceDetection()
ssd = SepSourceDetection()

pssd = PhotometryFocusSeries(SepSourceDetection, radius_column="kronrad")

pssd.reset()

for foc in [100, 50, 0, -50, -100]:
    await lvm.sci.foc.moveAbsolute(foc)
    ef, wf = (await lvm.sci.agc.expose(1)).flatten().unpack("east.filename", "west.filename")
    print (ef)
    print(wf)
    ei = Image.from_file(ef)
    wi = Image.from_file(wf)
    sei = await ssd(ei)
    dwi = await dsd(wi)
    await pssd.analyse_image(sei, foc+1000)

rc = pssd.fit_focus()

print(rc)




await invoke(lvm.sci.ag.status(), lvm.sci.pwi.status(),return_exceptions=True)
