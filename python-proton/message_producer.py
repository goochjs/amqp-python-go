#!/usr/bin/python3
'''
Created on 11th Jan 2017

@author: Jeremy Gooch

    Python AMQP message producer.

    Execute script with -h parameter for usage
'''

# --- LIBRARIES --------------------------------------------------------------

import sys
if sys.version_info[0] < 3:
    raise Exception("Python 3 or a more recent version is required.")

import argparse
import time
import datetime
import re
import uuid
import logging

from proton import Message
from proton.handlers import MessagingHandler
from proton.reactor import Container

# --- FUNCTIONS --------------------------------------------------------------

def process_options():
    '''
    Processes command line options
    '''

    opts = argparse.ArgumentParser(description="AMQP message producer.  Will connect to a broker and publish messages until stopped.")

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
        required=False,
        help="number of messages to send")
    opts.add_argument("--persistent", "-p",
        required=False,
        default=False,
        action="store_true",
        help="send persistent messages")
    opts.add_argument("--subject", "-s",
        required=False,
        help="message subject (adds header if included)")
    opts.add_argument("--user_id", "-u",
        required=False,
        help="client user id")
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
        options.persistent,
        options.subject,
        options.user_id,
        log_level)


def clean_url(dirty_url):
    # removes ID and password from URL, if present
    if "@" in dirty_url:
        return dirty_url.split('@', 1)[1]
    else:
        return dirty_url


# --- CLASSES ----------------------------------------------------------------

class Send(MessagingHandler):
    def __init__(self, url, resource, messages, persistent, subject, user_id):
        super(Send, self).__init__()
        self.url = url
        self.resource = resource
        self.persistent = persistent
        self.subject = subject
        self.user_id = user_id
        self.sent = 0
        self.confirmed = 0
        self.total = messages


    def on_start(self, event):
        messaging_connection = event.container.connect(self.url)
        event.container.create_sender(messaging_connection, self.resource)


    def on_sendable(self, event):
        logging.debug(str(self.confirmed) + " messages sent")
        logging.debug("Connected to " + clean_url(self.url) + " " + self.resource)

        # encode the user_id if present
        if self.user_id:
            encoded_user_id = self.user_id.encode('utf-8')
        else:
            encoded_user_id = None

        while event.sender.credit and self.sent < self.total:
            msg = Message(
                id=(str(uuid.uuid4())),
                user_id=encoded_user_id,
                durable=self.persistent,
                subject=self.subject,
                creation_time=time.time(),
                body={'sequence':(self.sent+1)}
                )
            event.sender.send(msg)
            self.sent += 1


    def on_accepted(self, event):
        self.confirmed += 1
        if self.confirmed == self.total:
            logging.info(str(self.confirmed) + " messages sent")
            event.connection.close()


    def on_disconnected(self, event):
        self.sent = self.confirmed
        logging.info("Disconnected from " + clean_url(self.url))


# --- START OF MAIN ----------------------------------------------------------

def main():
    start_time = datetime.datetime.now()
    (broker, resource, max_messages, persistent, subject, user_id, log_level) = process_options()

    logging.basicConfig(
            level=log_level,
            format='[%(levelname)s] (%(threadName)-10s) %(message)s',
        )
    logging.debug(datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p") + " Started")

    try:
        Container(
                Send(broker, resource, max_messages, persistent, subject, user_id)
            ).run()
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received")

    exec_time = datetime.datetime.now() - start_time
    logging.info("Execution time " + str(exec_time))
    logging.debug(datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p") + " Finished")



# --- END OF MAIN ------------------------------------------------------------


if __name__ == "__main__":
    main()
