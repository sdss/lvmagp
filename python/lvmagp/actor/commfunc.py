from lvmagp.actor.internalfunc import *


# Functions intracting with other actors
# It starts with the instruments that the function interacts with. ex. "focus_", "tel_" ...

# Functions for focuser
class LVMFocuser:
    def __init__(self, focuser):
        if focuser == "test":
            self.lvmtan = "test.first.focus_stage"
        else:
            self.lvmtan = "lvm." + focuser + ".foc"

    async def getposition(self, command):
        cmd = await send_message(
            command, self.lvmtan, "getposition", returnval=True, body="Position"
        )
        return cmd

    async def moveabs(self, command, position):
        cmd = await send_message(command, self.lvmtan, "moveabsolute %d" % position)
        return True


class LVMTelescope:
    def __init__(self, tel):
        if tel == "test":
            self.lvmpwi = "lvm.pwi"
        else:
            self.lvmpwi = "lvm." + tel + ".pwi"

    async def isslewing(self, command):
        cmd = await send_message(
            command, self.lvmpwi, "status", returnval=True, body="is_slewing"
        )
        return cmd

    async def slew_radec2000(self, command, target_ra_h, target_dec_d):
        cmd = await send_message(
            command,
            self.lvmpwi,
            "goto-ra-dec-j2000 %f %f" % (target_ra_h, target_dec_d),
        )
        return True

    async def wait_for_slew(self, command):
        while 1:
            isslew = await send_message(
                command, self.lvmpwi, "status", returnval=True, body="is_slewing"
            )
            if isslew:  ##one-way comm. of PWI4: warning.
                await asyncio.sleep(0.5)
            else:
                break
        return True

    async def offset_radec(self, command, ra_arcsec, dec_arcsec):
        if (ra_arcsec == 0) & (dec_arcsec == 0):
            raoffsetcmd = await send_message(
                command, self.lvmpwi, "offset --ra_reset 0"
            )
            await self.wait_for_slew(command)
            decoffsetcmd = await send_message(
                command, self.lvmpwi, "offset --dec_reset 0"
            )
            await self.wait_for_slew(command)

        else:
            raoffsetcmd = await send_message(
                command, self.lvmpwi, "offset --ra_add_arcsec %f" % ra_arcsec
            )
            await self.wait_for_slew(command)
            decoffsetcmd = await send_message(
                command, self.lvmpwi, "offset --dec_add_arcsec %f" % dec_arcsec
            )
            await self.wait_for_slew(command)

        return True


# Functions for camera
class LVMCamera:
    def __init__(self, tel):
        self.lvmcam = "lvmcam"

    async def single_exposure(self, command, cam, exptime):
        cmd = await send_message(
            command, self.lvmcam, "expose %f 1 %s" % (exptime, cam)
        )
        return True
