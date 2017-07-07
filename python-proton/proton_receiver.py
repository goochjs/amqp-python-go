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
from proton.reactor import Container, DurableSubscription

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
    opts.add_argument("--subscription_name", "-n",
        required=False,
        help="subscription name (durable)")
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

    if options.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    return(
        options.broker,
        resource,
        options.max_messages,
        options.subscription_name,
        log_level)


def clean_url(dirty_url):
    # removes ID and password from URL, if present
    if "@" in dirty_url:
        return dirty_url.split('@', 1)[1]
    else:
        return dirty_url


# --- CLASSES ----------------------------------------------------------------

class Recv(MessagingHandler):
    def __init__(self, url, resource, count, subscription_name):
        super(Recv, self).__init__()
        self.url = url
        self.resource = resource
        self.expected = count
        self.subscription_name = subscription_name
        self.received = []
        self.count = 0


    def on_start(self, event):
        if self.subscription_name:
            logging.debug("Naming durable subscription %s", self.subscription_name)
            durable = DurableSubscription()
        else:
            logging.debug("Subscription will not be durable")
            durable = None

        event.container.container_id = self.subscription_name

        messaging_connection = event.container.connect(self.url)
        event.container.create_receiver(
            messaging_connection,
            self.resource,
            name=self.subscription_name,
            options=durable
        )
        logging.debug("Connected to %s %s", clean_url(self.url), self.resource)


    def on_message(self, event):
        global first_message_time

        if self.count == 0:
            first_message_time = datetime.datetime.now()

        if event.message.id and event.message.id in self.received:
            logging.error("Duplicate message received %s", event.message.body)
            return

        # print the message out
        logging.debug(event.message)

        self.count += 1
        if event.message.id:
            self.received.append(event.message.id)

        if self.count == self.expected:
            if self.subscription_name:
                event.receiver.detach()
            else:
                event.receiver.close()

            event.connection.close()

            message_processing_time = datetime.datetime.now() - first_message_time
            logging.info("%s messages received in %s", self.count, message_processing_time)
            logging.debug("Disconnected from %s", clean_url(self.url))


# --- START OF MAIN ----------------------------------------------------------

def main():
    start_time = datetime.datetime.now()
    (broker, resource, max_messages, subscription_name, log_level) = process_options()

    logging.basicConfig(
            level=log_level,
            format='[%(levelname)s] (%(threadName)-10s) %(message)s',
        )
    logging.debug("%s Started", datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"))

    try:
        Container(Recv(broker, resource, max_messages, subscription_name)).run()
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received")
    except Exception as e:
        raise e

    exec_time = datetime.datetime.now() - start_time
    logging.debug("Execution time %s", exec_time)
    logging.debug("%s Finished", datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"))



# --- END OF MAIN ------------------------------------------------------------


if __name__ == "__main__":
    # initialise first message time (global variable used to calculate timings)
    first_message_time = datetime.datetime.now()

    main()
