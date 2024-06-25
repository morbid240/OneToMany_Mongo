# borrowed from: https://docs.mongoengine.org/guide/logging-monitoring.html
import logging
from pymongo import monitoring
from menu_definitions import menu_logging


log = logging.getLogger("MongoDB logger")
log_level: int = eval(menu_logging.menu_prompt())
log.setLevel(log_level)
logging.basicConfig(level=log_level)


class CommandLogger(monitoring.CommandListener):

    def started(self, event):
        log.debug("Command {0.command_name} with request id "
                  "{0.request_id} started on server "
                  "{0.connection_id}".format(event))

    def succeeded(self, event):
        log.debug("Command {0.command_name} with request id "
                  "{0.request_id} on server {0.connection_id} "
                  "succeeded in {0.duration_micros} "
                  "microseconds".format(event))

    def failed(self, event):
        log.debug("Command {0.command_name} with request id "
                  "{0.request_id} on server {0.connection_id} "
                  "failed in {0.duration_micros} "
                  "microseconds".format(event))
