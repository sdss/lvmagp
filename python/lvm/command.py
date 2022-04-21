# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: command.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import json

class LoggerCommand():
    def __init__(self, logger):
        self.logger = logger
       
    def finish(self, *args, **kwargs):
        """Convenience method to mark a command `~.CommandStatus.DONE`."""
        self.logger.info(f"{json.dumps(kwargs, sort_keys=True, indent=2)}")
 
    def fail(self, *args, **kwargs):
        """Convenience method to mark a command `~.CommandStatus.FAILED`."""

        self.logger.error(f"{json.dumps(kwargs, sort_keys=True, indent=2)}")

    def debug(self, *args, **kwargs):
        """Writes a debug-level message."""

        self.logger.debug(f"{json.dumps(kwargs, sort_keys=True, indent=2)}")

    def info(self, *args, **kwargs):
        """Writes an info-level message."""
        self.logger.info(f"{json.dumps(kwargs, sort_keys=True, indent=2)}")

    def warning(self, *args, **kwargs):
        """Writes a warning-level message."""

        self.logger.warning(f"{json.dumps(kwargs, sort_keys=True, indent=2)}")

    def error(self, *args, **kwargs):
        """Writes an error-level message (does not fail the command)."""

        self.logger.error(f"{json.dumps(kwargs, sort_keys=True, indent=2)}")


