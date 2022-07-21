
import asyncio

from cluplus.proxy import invoke
from lvmtipo.actors import lvm

from lvmagp.images import Image
from lvmagp.images.processors.detection import DaophotSourceDetection, SepSourceDetection
from lvmagp.images.processors.astrometry import AstrometryDotNet
from lvmagp.focus.focusseries import PhotometryFocusSeries, ProjectionFocusSeries


await lvm.sci.start()

await invoke(lvm.sci.foc.status(), lvm.sci.km.status(), lvm.sci.pwi.status())

ef, wf = (await lvm.sci.agc.expose(1)).flatten().unpack("east.filename", "west.filename")

sd = DaophotSourceDetection()
sd = SepSourceDetection()

ei = await sd(Image.from_file(ef))
wi = await sd(Image.from_file(wf))


pfs=PhotometryFocusSeries(SepSourceDetection)

pfs.analyse_image(ei,-400)



await invoke(lvm.sci.ag.status(), lvm.sci.pwi.status(),return_exceptions=True)
