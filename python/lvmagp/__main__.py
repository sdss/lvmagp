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

from lvmagp.actor.actor import LvmagpActor


@click.group(cls=DefaultGroup, default="actor")
@click.option(
    "-c",
    "--config",
    "config_file",
    type=click.Path(exists=True, dir_okay=False),
    help="Path to the user configuration file.",
    required=True
)
@click.option(
    "-r",
    "--rmq_url",
    "rmq_url",
    default=None,
    type=str,
    help="rabbitmq url, eg: amqp://guest:guest@localhost:5672/",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Debug mode. Use additional v for more details.",
)
@click.pass_context
def lvmagp(ctx, config_file, rmq_url, verbose):
    """lvm controller"""

    ctx.obj = {"verbose": verbose, "config_file": config_file, "rmq_url": rmq_url}


@lvmagp.group(cls=DaemonGroup, prog="lvmagp_actor", workdir=os.getcwd())
@click.pass_context
@cli_coro_lvm
async def actor(ctx):
    """Runs the actor."""

    config_file = ctx.obj["config_file"]

    lvmagp_obj = LvmagpActor.from_config(config_file, url=ctx.obj["rmq_url"], verbose=ctx.obj["verbose"])

    await lvmagp_obj.start()
    await lvmagp_obj.run_forever()


if __name__ == "__main__":
    lvmagp()
