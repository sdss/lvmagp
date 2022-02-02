# lvmagp

[![Versions](https://img.shields.io/badge/python->3.7-blue)](https://img.shields.io/badge/python->3.7-blue)
[![Documentation Status](https://readthedocs.org/projects/sdss-lvmagp/badge/?version=latest)](https://sdss-lvmagp.readthedocs.io/en/latest/?badge=latest)
[![Travis (.org)](https://img.shields.io/travis/sdss/lvmagp)](https://travis-ci.org/sdss/lvmagp)
[![codecov](https://codecov.io/gh/sdss/lvmagp/branch/main/graph/badge.svg)](https://codecov.io/gh/sdss/lvmagp)

lvmagp which controls focuser, guide camera and mount. 

## Prerequisite

Install [CLU](https://clu.readthedocs.io/en/latest/) by using PyPI.
```
$ pip install sdss-clu
```

Install [RabbitMQ](https://www.rabbitmq.com/) by using apt-get.

```
$ sudo apt-get install -y erlang
$ sudo apt-get install -y rabbitmq-server
$ sudo systemctl enable rabbitmq-server
$ sudo systemctl start rabbitmq-server
```

Install [pyenv](https://github.com/pyenv/pyenv) by using [pyenv installer](https://github.com/pyenv/pyenv-installer).

```
$ curl https://pyenv.run | bash
```

You should add the code below to `~/.bashrc` by using your preferred editor.
```
# pyenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"
```

Also you need other actors for hardware communication, which are [lvmtan](https://github.com/sdss/lvmtan), [lvmpwi](https://github.com/sdss/lvmpwi) and [lvmcam](https://github.com/sdss/lvmcam).
(Currently you only need lvmtan.)

## Quick start

### Installation

Clone this repository.
```
$ git clone https://github.com/sdss/lvmagp
$ cd lvmagp
```

Set the python 3.9.1 virtual environment.
```
$ pyenv install 3.9.1
$ pyenv virtualenv 3.9.1 lvmagp-env
$ pyenv local lvmagp-env
```

Install [poetry](https://python-poetry.org/) and dependencies.
```
$ pip install poetry
$ python create_setup.py
$ pip install -e .
```

### Ping-pong test
Start `lvmagp` actor.
```
$ lvmagp start
```

In another terminal, type `clu` and `lvmagp ping` for test.
```
$ clu
lvmagp ping
07:41:22.636 lvmagp > 
07:41:22.645 lvmagp : {
    "text": "Pong."
}
```

Stop `lvmagp` actor.
```
$ lvmagp stop
```
