
from lvmtipo.actors import lvm
from lvmagp.focus import Focus
from logging import DEBUG, INFO

telsubsys = await lvm.from_string("sci")
focus = Focus(telsubsys, level = DEBUG)

await focus.fine()
await focus.fine(guess=44, count=2, step=4, exposure_time=5)

