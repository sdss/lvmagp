
from logging import DEBUG, INFO

from lvmtipo.actors import lvm
from lvmagp.focus import Focus
from lvmagp.images import Image

telsubsys = await lvm.from_string("sci")
focus = Focus(telsubsys, level = DEBUG)


def img_cb(img_e, img_w):
    print(img_e.catalog)
    print(img_w.catalog)

await focus.fine(callback=img_cb)
await focus.fine(guess=44, count=2, step=4, exposure_time=5, callback=img_cb)


