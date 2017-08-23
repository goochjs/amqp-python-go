#!/usr/bin/python3
'''
Created on 4th July 2017

@author: Jeremy Gooch

    Python AMQP 0-9-1 message receiver.

    Execute script with -h parameter for usage
'''

# --- CONSTANTS --------------------------------------------------------------

CACERTFILE = "/mnt/ssl/ca/cacert.pem"
CERTFILE   = "/mnt/ssl/client/cert.pem"
KEYFILE    = "/mnt/ssl/client/key.pem"


# --- LIBRARIES --------------------------------------------------------------

import sys
if sys.version_info[0] < 3:
    raise Exception("Python 3 or a more recent version is required.")

import argparse
import datetime
import re
import logging
import os

import pika
from pika.credentials import ExternalCredentials
import ssl
from urllib.parse import urlparse

# --- FUNCTIONS --------------------------------------------------------------

def process_options():
    '''
    Processes command line options
    '''

    opts = argparse.ArgumentParser(description="AMQP message producer.  Will connect to a broker and retrieve messages until stopped.")

    opts.add_argument("--broker", "-b",
        required=False,
        default="amqp://localhost:5672",
        help="broker connection string")
    opts.add_argument("--exchange", "-e",
        required=False,
        help="exchange name (is set to queue/topic name if omitted)")
    opts.add_argument("--max_messages", "-m",
        type=int,
        default=100,
        required=True,
        help="number of messages to receive before stopping. Setting '0' retrieves indefinitely")
    opts.add_argument("--queue", "-q",
        required=False,
        help="queue name")
    opts.add_argument("--topic", "-t",
        required=False,
        help="topic name")
    opts.add_argument("--verbose", "-v",
        required=False,
        default=False,
        action="store_true",
        help="send log messages to sysout")
    options = opts.parse_args()

    # Check that the connection string looks sensible
    checkConnection = re.match('amqp(s?):\/\/(.*):\d{1,5}$', options.broker, )
    if not(checkConnection):
        opts.error("The broker connection string looks a bit dodgy.  It should be something like 'amqp://localhost:5672'")

    # set up the queue name and binding key
    if options.topic:
        binding_key = options.topic

        # if no queue provided then set the queue name to the same as the topic
        if options.queue:
            queue_name = options.queue
        else:
            queue_name = options.topic
    else:
        binding_key = options.queue
        queue_name = options.queue

    # if no explicit exchange parameter was specified, set it to the same as the binding key
    if options.exchange:
        exchange = options.exchange
    else:
        exchange = binding_key

    if options.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    return(
        options.broker,
        exchange,
        binding_key,
        queue_name,
        options.max_messages,
        log_level)


def clean_url(dirty_url):
    # removes ID and password from URL, if present
    if "@" in dirty_url:
        return dirty_url.split('@', 1)[1]
    else:
        return dirty_url


# --- CLASSES ----------------------------------------------------------------

class Consumer(object):
    """This consumer will handle unexpected interactions with RabbitMQ such
    as channel and connection closures.

    If RabbitMQ closes the connection, it will reopen it. You should
    look at the output, as there are limited reasons why the connection may
    be closed, which usually are tied to permission related issues or
    socket timeouts.

    If the channel is closed, it will indicate a problem with one of the
    commands that were issued and that should surface in the output as well.

    """
    _WAIT_INTERVAL = 20   # number of seconds to wait before retrying connection


    def __init__(self, amqp_url, exchange, binding_key, queue_name, max_messages):
        """Create a new instance of the consumer class, passing in the AMQP
        URL used to connect to RabbitMQ.

        :param str amqp_url: The AMQP url to connect with
        :param str binding_key: The name of the binding key

        """
        self._connection = None
        self._channel = None
        self._closing = False
        self._consumer_tag = None
        self._url = amqp_url
        self._binding_key = binding_key
        self._exchange = exchange
        self._queue = queue_name
        self._max_messages = max_messages
        self._count = 0
        self._first_message_time = datetime.datetime.now()



    def connect(self):
        """This method connects to RabbitMQ, returning the connection handle.
        When the connection is established, the on_connection_open method
        will be invoked by pika.

        :rtype: pika.SelectConnection

        """
        logging.debug('Connecting to %s', clean_url(self._url))

        # pull the url apart
        parsed_url = urlparse(self._url)

        if parsed_url.scheme == "amqps":
            for f in [CACERTFILE, CERTFILE, KEYFILE]:
                if not os.path.isfile(f):
                    raise Exception(f + " does not exist")

            # set up SSL connection
            ssl_options = ({"ca_certs": CACERTFILE,
                    "certfile": CERTFILE,
                    "keyfile": KEYFILE,
                    "ssl_version": ssl.PROTOCOL_TLSv1_2,
                    "cert_reqs": ssl.CERT_REQUIRED})

            params = pika.ConnectionParameters(
                    host=parsed_url.hostname,
                    port=parsed_url.port,
                    credentials=ExternalCredentials(),
                    ssl=True,
                    ssl_options=ssl_options,
                    connection_attempts=10,
                    heartbeat_interval=3600,
                    socket_timeout=5)

        else:
            # set up non-SSL connection
            credentials = pika.PlainCredentials(parsed_url.username, parsed_url.password)

            params = pika.ConnectionParameters(
                    host=parsed_url.hostname,
                    port=parsed_url.port,
                    credentials=credentials,
                    connection_attempts=100,
                    heartbeat_interval=3600,
                    socket_timeout=5)

        return pika.SelectConnection(params,
                                    self.on_connection_open,
                                    stop_ioloop_on_close=False)


    def on_connection_open(self, unused_connection):
        """This method is called by pika once the connection to RabbitMQ has
        been established. It passes the handle to the connection object in
        case we need it, but in this case, we'll just mark it unused.

        :type unused_connection: pika.SelectConnection

        """
        logging.debug('Connection opened')
        self.add_on_connection_close_callback()
        self.open_channel()


    def add_on_connection_close_callback(self):
        """This method adds an on close callback that will be invoked by pika
        when RabbitMQ closes the connection to the publisher unexpectedly.

        """
        logging.debug('Adding connection close callback')
        self._connection.add_on_close_callback(self.on_connection_closed)


    def on_connection_closed(self, connection, reply_code, reply_text):
        """This method is invoked by pika when the connection to RabbitMQ is
        closed unexpectedly. Since it is unexpected, we will reconnect to
        RabbitMQ if it disconnects.

        :param pika.connection.Connection connection: The closed connection obj
        :param int reply_code: The server provided reply_code if given
        :param str reply_text: The server provided reply_text if given

        """
        self._channel = None
        if self._closing:
            self._connection.ioloop.stop()
        else:
            logging.warning('Connection closed, reopening in %s seconds: (%s) %s',
                           self._WAIT_INTERVAL, reply_code, reply_text)
            self._connection.add_timeout(self._WAIT_INTERVAL, self.reconnect)


    def reconnect(self):
        """Will be invoked by the IOLoop timer if the connection is
        closed. See the on_connection_closed method.

        """
        # This is the old connection IOLoop instance, stop its ioloop
        self._connection.ioloop.stop()

        if not self._closing:

            # Create a new connection
            self._connection = self.connect()

            # There is now a new connection, needs a new ioloop to run
            self._connection.ioloop.start()


    def open_channel(self):
        """Open a new channel with RabbitMQ by issuing the Channel.Open RPC
        command. When RabbitMQ responds that the channel is open, the
        on_channel_open callback will be invoked by pika.

        """
        logging.debug('Creating a new channel')
        self._connection.channel(on_open_callback=self.on_channel_open)


    def on_channel_open(self, channel):
        """This method is invoked by pika when the channel has been opened.
        The channel object is passed in so we can make use of it.

        Since the channel is now open, we'll declare the exchange to use.

        :param pika.channel.Channel channel: The channel object

        """
        logging.debug('Channel opened')
        self._channel = channel
        self.add_on_channel_close_callback()
        self.setup_queue(self._queue)


    def add_on_channel_close_callback(self):
        """This method tells pika to call the on_channel_closed method if
        RabbitMQ unexpectedly closes the channel.

        """
        logging.debug('Adding channel close callback')
        self._channel.add_on_close_callback(self.on_channel_closed)


    def on_channel_closed(self, channel, reply_code, reply_text):
        """Invoked by pika when RabbitMQ unexpectedly closes the channel.
        Channels are usually closed if you attempt to do something that
        violates the protocol, such as re-declare an exchange or queue with
        different parameters. In this case, we'll close the connection
        to shutdown the object.

        :param pika.channel.Channel: The closed channel
        :param int reply_code: The numeric reason the channel was closed
        :param str reply_text: The text reason the channel was closed

        """
        logging.warning('Channel %i was closed: (%s) %s',
                       channel, reply_code, reply_text)
        self._connection.close()


    def setup_queue(self, queue_name):
        """Setup the queue on RabbitMQ by invoking the Queue.Declare RPC
        command. When it is complete, the on_queue_declareok method will
        be invoked by pika.

        :param str|unicode queue_name: The name of the queue to declare.

        """
        logging.debug('Declaring queue %s', queue_name)
        self._channel.queue_declare(self.on_queue_declareok,
                                    queue_name,
                                    False,
                                    True)


    def on_queue_declareok(self, method_frame):
        """Method invoked by pika when the Queue.Declare RPC call made in
        setup_queue has completed. In this method we will bind the queue
        and exchange together with the routing key by issuing the Queue.Bind
        RPC command. When this command is complete, the on_bindok method will
        be invoked by pika.

        :param pika.frame.Method method_frame: The Queue.DeclareOk frame

        """
        logging.info('Binding %s to %s with %s',
                    self._exchange, self._queue, self._binding_key)
        self._channel.queue_bind(self.on_bindok, self._queue,
                                 self._exchange, self._binding_key)


    def on_bindok(self, unused_frame):
        """Invoked by pika when the Queue.Bind method has completed. At this
        point we will start consuming messages by calling start_consuming
        which will invoke the needed RPC commands to start the process.

        :param pika.frame.Method unused_frame: The Queue.BindOk response frame

        """
        logging.debug('Queue bound')
        self.start_consuming()


    def start_consuming(self):
        """This method sets up the consumer by first calling
        add_on_cancel_callback so that the object is notified if RabbitMQ
        cancels the consumer. It then issues the Basic.Consume RPC command
        which returns the consumer tag that is used to uniquely identify the
        consumer with RabbitMQ. We keep the value to use it when we want to
        cancel consuming. The on_message method is passed in as a callback pika
        will invoke when a message is fully received.

        """
        logging.debug('Issuing consumer related RPC commands')
        self.add_on_cancel_callback()
        self._consumer_tag = self._channel.basic_consume(self.on_message,
                                                         self._queue)


    def add_on_cancel_callback(self):
        """Add a callback that will be invoked if RabbitMQ cancels the consumer
        for some reason. If RabbitMQ does cancel the consumer,
        on_consumer_cancelled will be invoked by pika.

        """
        logging.debug('Adding consumer cancellation callback')
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)


    def on_consumer_cancelled(self, method_frame):
        """Invoked by pika when RabbitMQ sends a Basic.Cancel for a consumer
        receiving messages.

        :param pika.frame.Method method_frame: The Basic.Cancel frame

        """
        logging.debug('Consumer was cancelled remotely, shutting down: %r',
                    method_frame)
        if self._channel:
            self._channel.close()


    def on_message(self, unused_channel, basic_deliver, properties, body):
        """Invoked by pika when a message is delivered from RabbitMQ. The
        channel is passed for your convenience. The basic_deliver object that
        is passed in carries the exchange, routing key, delivery tag and
        a redelivered flag for the message. The properties passed in is an
        instance of BasicProperties with the message properties and the body
        is the message that was sent.

        :param pika.channel.Channel unused_channel: The channel object
        :param pika.Spec.Basic.Deliver: basic_deliver method
        :param pika.Spec.BasicProperties: properties
        :param str|unicode body: The message body

        """
        if self._count == 0:
            self._first_message_time = datetime.datetime.now()

        logging.debug("Message received %s %s %s", properties, basic_deliver, body)

        logging.debug('Acknowledging message %s', basic_deliver.delivery_tag)
        self._channel.basic_ack(basic_deliver.delivery_tag)

        # the following code can be uncommented in place of the ack above
        # in order to test dead letter processing
        #self._channel.basic_nack(
        #    delivery_tag=basic_deliver.delivery_tag,
        #    requeue=False)

        self._count += 1

        if self._count == self._max_messages:
            message_processing_time = datetime.datetime.now() - self._first_message_time
            logging.info("%s messages received in %s (%s/s)",
                self._count,
                message_processing_time,
                round(self._count/message_processing_time.total_seconds(), 2))

            self.stop()

            logging.debug("Disconnected from %s", clean_url(self._url))


    def stop_consuming(self):
        """Tell RabbitMQ that you would like to stop consuming by sending the
        Basic.Cancel RPC command.

        """
        if self._channel:
            logging.debug('Sending a Basic.Cancel RPC command to RabbitMQ')
            self._channel.basic_cancel(self.on_cancelok, self._consumer_tag)


    def on_cancelok(self, unused_frame):
        """This method is invoked by pika when RabbitMQ acknowledges the
        cancellation of a consumer. At this point we will close the channel.
        This will invoke the on_channel_closed method once the channel has been
        closed, which will in-turn close the connection.

        :param pika.frame.Method unused_frame: The Basic.CancelOk frame

        """
        logging.debug('RabbitMQ acknowledged the cancellation of the consumer')
        self.close_channel()


    def close_channel(self):
        """Call to close the channel with RabbitMQ cleanly by issuing the
        Channel.Close RPC command.

        """
        logging.debug('Closing the channel')
        self._channel.close()


    def run(self):
        """Run the example consumer by connecting to RabbitMQ and then
        starting the IOLoop to block and allow the SelectConnection to operate.

        """
        self._connection = self.connect()
        self._connection.ioloop.start()


    def stop(self):
        """Cleanly shutdown the connection to RabbitMQ by stopping the consumer
        with RabbitMQ. When RabbitMQ confirms the cancellation, on_cancelok
        will be invoked by pika, which will then closing the channel and
        connection. The IOLoop is started again because this method is invoked
        when CTRL-C is pressed raising a KeyboardInterrupt exception. This
        exception stops the IOLoop which needs to be running for pika to
        communicate with RabbitMQ. All of the commands issued prior to starting
        the IOLoop will be buffered but not processed.

        """
        logging.info('Stopping')
        self._closing = True
        self.stop_consuming()
        self._connection.ioloop.start()
        logging.debug('Stopped')


    def close_connection(self):
        """This method closes the connection to RabbitMQ."""
        logging.debug('Closing connection')
        self._connection.close()


# --- START OF MAIN ----------------------------------------------------------

def main():
    start_time = datetime.datetime.now()
    (broker, exchange, binding_key, queue_name, max_messages, log_level) = process_options()

    logging.basicConfig(
            level=log_level,
            format='[%(levelname)s] (%(threadName)-10s) %(message)s',
        )
    logging.debug(datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p") + " Started")

    conn = Consumer(
            broker,
            exchange,
            binding_key,
            queue_name,
            max_messages
        )

    try:
        conn.run()
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received")
        conn.stop()
    except Exception as e:
        raise e

    exec_time = datetime.datetime.now() - start_time
    logging.info("Execution time %s", exec_time)
    logging.debug(datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p") + " Finished")



# --- END OF MAIN ------------------------------------------------------------


if __name__ == "__main__":
    # initialise first message time (global variable used to calculate timings)
    first_message_time = datetime.datetime.now()

    main()
