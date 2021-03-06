#!/usr/bin/env python
# encoding: utf-8
#
# @Author: José Sánchez-Gallego
# @Date: Dec 1, 2017
# @Filename: cli.py
# @License: BSD 3-Clause
# @Copyright: José Sánchez-Gallego

import os

import click
from click_default_group import DefaultGroup
from clu.tools import cli_coro as cli_coro_lvm

from sdsstools.daemonizer import DaemonGroup

from lvmagp.actor.actor import lvmagp as lvmagpInstance


@click.group(cls=DefaultGroup, default="actor", default_if_no_args=True)
@click.option(
    "-c",
    "--config",
    "config_file",
    type=click.Path(exists=True, dir_okay=False),
    help="Path to the user configuration file.",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Debug mode. Use additional v for more details.",
)
@click.pass_context
def lvmagp(ctx, config_file, verbose):
    """lvm controller"""

    ctx.obj = {"verbose": verbose, "config_file": config_file}


@lvmagp.group(cls=DaemonGroup, prog="lvmagp_actor", workdir=os.getcwd())
@click.pass_context
@cli_coro_lvm
async def actor(ctx):
    """Runs the actor."""

    default_config_file = os.path.join(os.path.dirname(__file__), "etc/lvmagp.yml")
    config_file = ctx.obj["config_file"] or default_config_file

    lvmagp_obj = lvmagpInstance.from_config(config_file)
    if ctx.obj["verbose"]:
        lvmagp_obj.log.fh.setLevel(0)
        lvmagp_obj.log.sh.setLevel(0)
    await lvmagp_obj.start()
    await lvmagp_obj.run_forever()


if __name__ == "__main__":
    lvmagp()
