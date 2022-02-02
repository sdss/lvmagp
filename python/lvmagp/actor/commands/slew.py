import click
from clu.command import Command

from lvmagp.actor.commfunc import LVMTelescopeUnit

from . import parser


@parser.command()
@click.argument("TEL", type=str)
@click.argument("TARGET_RA_H", type=float)
@click.argument("TARGET_DEC_D", type=float)
async def slew(
    command: Command,
    tel: str,
    target_ra_h: float,
    target_dec_d: float,
):
    """
    Slew the telescope to the given equatorial coordinate (J2000).

    Parameters
    ----------
    tel
        Telescope to slew
    target_ra_h
        The right ascension (J2000) of the target in hours
    target_dec_d
        The declination (J2000) of the target in degrees
    """

    telunit = LVMTelescopeUnit(tel)
    telunit.slew_radec2000(target_ra_h=target_ra_h, target_dec_d=target_dec_d)
    del telunit

    return command.finish(text="Acquisition done")
