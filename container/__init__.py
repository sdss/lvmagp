import subprocess
# import sys
import os
# import time
# import pexpect
import shlex
import click
import socket
from pathlib import PosixPath

container_bin = 'podman'
lvmt_root = os.environ["PWD"]
lvmt_image_source_local = "localhost/sdss"
lvmt_image_source_remote = "ghcr.io/sdss"
lvmt_image_name = 'lvmagp'
lvmt_rmq = socket.gethostname()

default_agp = 'lvm.agp'

# def isRunning(name: str = default_agp):
#     command = subprocess.run(shlex.split(f"{container_bin} container exists {name}"))
#     return not command.returncode # True if running

# def next_free_port( port=5900, max_port=5909 ):
#     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     while port <= max_port:
#         try:
#             sock.bind(('', port))
#             sock.close()
#             return port
#         except OSError:
#             port += 1
#     print('no free ports')
#     return None

@click.command()   
@click.option("--lvmt_root", default=lvmt_root, type=str)
@click.option("--use-cache/--no-cache", default=True)
def build(lvmt_root:str, use_cache: bool):
    agp_dockerfile = f"{lvmt_root}/container"
    lvmt_image_fullbuild = "" if use_cache else " --no-cache"
    build = f"{container_bin} build --tag sdss/{lvmt_image_name} {lvmt_image_fullbuild} --rm {agp_dockerfile} --format docker"
    print(build)
    command = subprocess.run(shlex.split(build))


@click.command()   
@click.option("--lvmt_root", default=lvmt_root, type=str)
@click.option("--name", "-n", default=default_agp, type=str)
@click.option("--debug/--no-debug", "-d", default=False)
@click.option("--kill/--no-kill", default=False)
@click.option("--rmq", default=lvmt_rmq, type=str)
@click.option("--simulator/--aravisagp", default=False)
def start(lvmt_root:str, name: str, debug:bool, kill:bool, rmq:str, simulator:bool):
    if not subprocess.run(shlex.split(f"podman image exists {lvmt_image_source_local}/{lvmt_image_name}")).returncode:
       lvmt_image = f"{lvmt_image_source_local}/{lvmt_image_name}"
    else:
       if subprocess.run(shlex.split(f"podman image exists {lvmt_image_source_remote}/{lvmt_image_name}")).returncode:
           subprocess.run(shlex.split(f"podman pull {lvmt_image_source_remote}/{lvmt_image_name}:latest"))
       lvmt_image = f"{lvmt_image_source_remote}/{lvmt_image_name}"


    if kill:
        subprocess.run(shlex.split(f"podman kill {name}"))
        subprocess.run(shlex.split(f"podman rm {name} -f"))

        
    run_base = f"--rm -d --name={name}"
    
    if rmq:
        run_base += f" -e LVMT_RMQ={lvmt_rmq}"
    else:
        run_base += f" -e LVMT_RMQ={socket.gethostname()}"

    if debug:
        run_base +=  f" -e LVMT_DEBUG=true"

    if simulator:
        run_base +=  f" -e LVMT_CAM_TYPE=skymakeragp"

    run_agp = f"-v {lvmt_root}/python/lvmagp:/root/lvmagp/python/lvmagp:rw -e LVMT_CAM={name}"
    run = f"{container_bin} run {run_base} {run_agp} {lvmt_image}"
    print(run)
    #child = pexpect.spawn(run)
    #child.expect('BSC loaded')
    #assert isRunning(name) == True
    command = subprocess.run(shlex.split(f"{run}"))
    logs = subprocess.run(shlex.split(f"podman logs -f {name}"))
    
    print("done")

@click.command()   
@click.option("--name", "-n", default=default_agp, type=str)
def stop(name: str):
    command = subprocess.run(shlex.split(f"{container_bin} kill {name}"))

