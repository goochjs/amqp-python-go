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
import logging
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

    opts.add_argument("--broker", "-b",
        required=False,
        default="localhost:5672",
        help="broker connection string")
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
    checkConnection = re.match('(.*):\d{1,5}', options.broker, )
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
        options.broker,
        resource,
        options.max_messages,
        options.verbose)


# --- CLASSES ----------------------------------------------------------------

class Recv(MessagingHandler):
    def __init__(self, url, resource, count):
        super(Recv, self).__init__()
        self.url = url
        self.resource = resource
        self.expected = count
        self.received = []
        self.count = 0


    def on_start(self, event):
        messaging_connection = event.container.connect(self.url)
        event.container.create_receiver(messaging_connection, self.resource)
        logging.debug("Connected to " + self.url + "/" + self.resource)


    def on_message(self, event):
        if event.message.id and event.message.id in self.received:
            logging.error("Duplicate message received " + str(event.message.body))
            return

        print(event.message)

        self.count += 1
        if event.message.id:
            self.received.append(event.message.id)

        if self.count == self.expected:
            event.receiver.close()
            event.connection.close()
            logging.debug(str(self.count) + " messages received")
            logging.debug("Disconnected from " + self.url)



# --- START OF MAIN ----------------------------------------------------------

def main():
    start_time = datetime.datetime.now()
    (broker, resource, max_messages, log_level) = process_options()

    logging.basicConfig(
            level=log_level,
            format='[%(levelname)s] (%(threadName)-10s) %(message)s',
        )
    logging.debug(datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p") + " Started")

    try:
        Container(Recv(broker, resource, max_messages)).run()
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received")

    exec_time = datetime.datetime.now() - start_time
    logging.debug("Execution time " + str(exec_time))
    logging.debug(datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p") + " Finished")



# --- END OF MAIN ------------------------------------------------------------


if __name__ == "__main__":
    main()
