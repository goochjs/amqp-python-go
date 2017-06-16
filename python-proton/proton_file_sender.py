#!/usr/bin/python3
'''
Created on 24th Apr 2017

@author: Jeremy Gooch

    Slightly hacky script to put the contents of a file onto a queue/topic.

    Execute script with -h parameter for usage
'''

# --- LIBRARIES --------------------------------------------------------------

import sys
if sys.version_info[0] < 3:
    raise Exception("Python 3 or a more recent version is required.")

import argparse
import time
import datetime
import os.path
import re
import uuid
import logging
import sys

from proton import Message
from proton.handlers import MessagingHandler
from proton.reactor import Container

# --- FUNCTIONS --------------------------------------------------------------

def process_options():
    '''
    Processes command line options
    '''

    opts = argparse.ArgumentParser(description="AMQP file sender.  Will connect to a broker and send a file line-by-line.")

    opts.add_argument("--file", "-f",
        required=True,
        help="file to be sent")
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
    opts.add_argument("--persistent", "-p",
        required=False,
        default=False,
        action="store_true",
        help="send persistent messages")
    opts.add_argument("--user_id", "-u",
        required=False,
        help="client user id")
    opts.add_argument("--header", "-a",
        action='append',
        required=False,
        help="header(s) to be added to the message - to be formatted as 'name=value'")
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
        options.file,
        options.broker,
        resource,
        options.persistent,
        options.user_id,
        options.header,
        log_level)


def clean_url(dirty_url):
    # removes ID and password from URL, if present
    if "@" in dirty_url:
        return dirty_url.split('@', 1)[1]
    else:
        return dirty_url


def parse_headers(headers):
    # takes the array of header parameters and returns a dict
    header_dict = {}

    for header in headers:
        logging.debug("Header " + header)

        # headers should have been specified as "name=value"
        if "=" in header:
            split_header = header.split('=', 1)
            header_dict[split_header[0]] = split_header[1]
        else:
            logging.warning("Header not structured 'name=value', ignoring parameter - " + header)

    return header_dict


# --- CLASSES ----------------------------------------------------------------

class Send(MessagingHandler):
    def __init__(self, filename, url, resource, persistent, user_id, headers):
        super(Send, self).__init__()
        self.filename = filename
        self.url = url
        self.resource = resource
        self.persistent = persistent
        self.user_id = user_id
        self.headers = headers


    def on_start(self, event):
        messaging_connection = event.container.connect(self.url)
        event.container.create_sender(messaging_connection, self.resource)


    def on_sendable(self, event):
        global send_count

        logging.debug(str(send_count) + " messages sent")
        logging.debug("Connected to " + clean_url(self.url) + " " + self.resource)

        # encode the user_id if present
        if self.user_id:
            encoded_user_id = self.user_id.encode('utf-8')
        else:
            encoded_user_id = None

        try:
            with open(self.filename, encoding='utf-8') as a_file:
                logging.debug("Opened file " + self.filename)

                for a_line in a_file:
                    msg = Message(
                        id=(str(uuid.uuid4())),
                        user_id=encoded_user_id,
                        durable=self.persistent,
                        properties=self.headers,
                        creation_time=time.time(),
                        body=a_line
                    )
                    event.sender.send(msg)

            event.connection.close()

        except IOError:
            logging.error("File not found " + self.filename)
            sys.exit()


    def on_accepted(self, event):
        global send_count
        send_count += 1


    def on_disconnected(self, event):
        logging.debug("Disconnected from " + clean_url(self.url))


# --- START OF MAIN ----------------------------------------------------------

def main():
    start_time = datetime.datetime.now()
    (filename, broker, resource, persistent, user_id, headers, log_level) = process_options()

    logging.basicConfig(
            level=log_level,
            format='[%(levelname)s] (%(threadName)-10s) %(message)s',
        )
    logging.debug(datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p") + " Started")

    try:
        Container(
                Send(filename, broker, resource, persistent, user_id, parse_headers(headers))
                ).run()
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received")

    exec_time = datetime.datetime.now() - start_time
    logging.info(str(send_count) + " messages sent in " + str(exec_time))
    logging.debug(datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p") + " Finished")



# --- END OF MAIN ------------------------------------------------------------


if __name__ == "__main__":
    send_count = 0
    main()
