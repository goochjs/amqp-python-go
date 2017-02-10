'''
Created on 11th Jan 2017

@author: Jeremy Gooch

    Python AMQP message producer.

    Execute script with -h parameter for usage
'''

# --- LIBRARIES --------------------------------------------------------------

import argparse
import time
import datetime
import sys
import re
import uuid

from proton import Message
from proton.handlers import MessagingHandler
from proton.reactor import Container

# --- FUNCTIONS --------------------------------------------------------------

def process_options():
    '''
    Processes command line options
    '''

    opts = argparse.ArgumentParser(description="AMQP message producer.  Will connect to a broker and publish messages until stopped.")

    opts.add_argument("--connection", "-c",
                      required=False,
                      default="localhost:5672",
                      help="connection string")
    opts.add_argument("--topic", "-t",
                      required=False,
                      help="topic name")
    opts.add_argument("--queue", "-q",
                      required=False,
                      help="queue name")
    opts.add_argument("--max_messages", "-m",
                      type=int,
                      default=100,
                      required=False,
                      help="number of messages to send")
    opts.add_argument("--persistent", "-p",
                      required=False,
                      default=False,
                      action="store_true",
                      help="send persistent messages")
    opts.add_argument("--verbose", "-v",
                      required=False,
                      default=False,
                      action="store_true",
                      help="send log messages to sysout")
    options = opts.parse_args()

    # Check that the connection string looks sensible
    checkConnection = re.match('(.*):\d{1,5}', options.connection, )
    if not(checkConnection):
        opts.error("The broker connection string looks a bit dodgy.  It should be something like 'localhost:5672'")

    # check that one and only one of topic or queue was specified
    if options.topic and options.queue:
        opts.error("You may only specify either a queue or a topic")
    if not(options.topic) and not(options.queue):
        opts.error("You must specify either a queue or a topic")

    # add the correct internal protocol
    if options.topic:
        resource = "topic://" + options.topic
    else:
        resource = "queue://" + options.queue

    return(options.connection, resource, options.max_messages, options.persistent, options.verbose)


# --- CLASSES ----------------------------------------------------------------

class Send(MessagingHandler):
    def __init__(self, url, resource, messages, persistent, logger):
        super(Send, self).__init__()
        self.url = url
        self.resource = resource
        self.persistent = persistent
        self.sent = 0
        self.confirmed = 0
        self.total = messages
        self.logger = logger


    def on_start(self, event):
        messaging_connection = event.container.connect(self.url)
        event.container.create_sender(messaging_connection, self.resource)


    def on_sendable(self, event):
        self.logger.log("Connected to " + self.url + "/" + self.resource)
        while event.sender.credit and self.sent < self.total:
            msg = Message(
                          id=(str(uuid.uuid4())),
                          durable=self.persistent,
                          creation_time=time.time(),
                          body={'sequence':(self.sent+1)}
                          )
            event.sender.send(msg)
            self.sent += 1


    def on_accepted(self, event):
        self.confirmed += 1
        if self.confirmed == self.total:
            self.logger.log(str(self.confirmed) + " messages sent")
            event.connection.close()


    def on_disconnected(self, event):
        self.sent = self.confirmed
        self.logger.log("Disconnected from " + self.url)


class script_logger(object):
    def __init__(self, log_flag):
        '''
        Script control class for logging messages (if required) and stopping execution
        '''

        self.log_flag = log_flag
        self.start_time = datetime.datetime.now()


    def log(self, log_message):
        '''
        Prints a timestamped log message
        '''

        if self.log_flag:
            time_stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            print (time_stamp + " " + log_message)


    def stop(self, log_message, exit_code, override_flag):
        '''
        Stops the script, logging an output message and setting a return code

        The override flag parameter will force a log message, even if the script has been called in non-logging mode
        '''

        if override_flag:
            self.log_flag = True

        self.log(log_message)
        exec_time = datetime.datetime.now() - self.start_time
        self.log("Execution time " + str(exec_time))
        self.log("Exiting with return code " + str(exit_code))
        sys.exit(exit_code)



# --- START OF MAIN ----------------------------------------------------------

def main():
    (connection, resource, max_messages, persistent, log_flag) = process_options()

    logger = script_logger(log_flag)
    logger.log("Started")

    try:
        Container(Send(connection, resource, max_messages, persistent, logger)).run()
    except KeyboardInterrupt:
        logger.log("Keyboard interrupt received")

    logger.stop("Finished", 0, False)



# --- END OF MAIN ------------------------------------------------------------


if __name__ == "__main__":
    main()
