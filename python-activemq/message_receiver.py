#!/usr/bin/python3
'''
Created on 13th Jan 2017

@author: Jeremy Gooch

    Python AMQP message receiver.

    Execute script with -h parameter for usage
'''

# --- LIBRARIES --------------------------------------------------------------

import sys
if sys.version_info[0] < 3:
    raise Exception("Python 3 or a more recent version is required.")

import argparse
import datetime
import re

from proton.handlers import MessagingHandler
from proton.reactor import Container

# --- FUNCTIONS --------------------------------------------------------------

def process_options():
    '''
    Processes command line options
    '''

    opts = argparse.ArgumentParser(description="AMQP message producer.  Will connect to a broker and retrieve messages until stopped.")

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
        required=True,
        help="number of messages to receive before stopping. Setting '0' retrieves indefinitely")
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

    return(
        options.connection,
        resource,
        options.max_messages,
        options.verbose)


# --- CLASSES ----------------------------------------------------------------

class Recv(MessagingHandler):
    def __init__(self, url, resource, count, logger):
        super(Recv, self).__init__()
        self.url = url
        self.resource = resource
        self.expected = count
        self.received = []
        self.count = 0
        self.logger = logger


    def on_start(self, event):
        messaging_connection = event.container.connect(self.url)
        event.container.create_receiver(messaging_connection, self.resource)
        self.logger.log("Connected to " + self.url + "/" + self.resource)


    def on_message(self, event):
        if event.message.id and event.message.id in self.received:
            self.logger.log("Duplicate message received " + str(event.message.body))
            return

        print(event.message)

        self.count += 1
        if event.message.id:
            self.received.append(event.message.id)

        if self.count == self.expected:
            event.receiver.close()
            event.connection.close()
            self.logger.log(str(self.count) + " messages received")
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
    (url, resource, max_messages, log_flag) = process_options()

    logger = script_logger(log_flag)
    logger.log("Started")

    try:
        Container(Recv(url, resource, max_messages, logger)).run()
    except KeyboardInterrupt:
        logger.log("Keyboard interrupt received")

    logger.stop("Finished", 0, False)



# --- END OF MAIN ------------------------------------------------------------


if __name__ == "__main__":
    main()
