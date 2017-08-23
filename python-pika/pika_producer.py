#!/usr/bin/python3
'''
Created on 9th June 2017

@author: Jeremy Gooch

    Python AMQP 0-9-1 message producer.

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
import time
import datetime
import re
import uuid
import logging
import os

import pika
from pika.credentials import ExternalCredentials
import json
import ssl
from urllib.parse import urlparse

# --- FUNCTIONS --------------------------------------------------------------

def process_options():
    '''
    Processes command line options
    '''

    opts = argparse.ArgumentParser(description="AMQP 0-9-1 message producer.  Will connect to a broker and publish messages until stopped.")

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
        required=False,
        help="number of messages to send")
    opts.add_argument("--persistent", "-p",
        required=False,
        default=False,
        action="store_true",
        help="send persistent messages")
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

    # check that one and only one of topic or queue was specified
    if options.topic and options.queue:
        opts.error("You may only specify either a queue or a topic")
    if not(options.topic) and not(options.queue):
        opts.error("You must specify either a queue or a topic")

    # add the correct exchange type
    if options.topic:
        routing_key = options.topic
        exchange_type = "topic"
    else:
        routing_key = options.queue
        exchange_type = "direct"

    # if no explicit exchange parameter was specified, set it to the same as the routing key
    if options.exchange:
        exchange = options.exchange
    else:
        exchange = routing_key

    if options.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    return(
        options.broker,
        routing_key,
        exchange,
        exchange_type,
        options.max_messages,
        options.persistent,
        log_level)


def clean_url(dirty_url):
    # removes ID and password from URL, if present
    if "@" in dirty_url:
        return dirty_url.split('@', 1)[1]
    else:
        return dirty_url


# --- CLASSES ----------------------------------------------------------------

class Publisher(object):
    """This publisher will handle unexpected interactions with a broker
    such as channel and connection closures.

    If the broker closes the connection, it will reopen it. You should
    look at the output, as there are limited reasons why the connection may
    be closed, which usually are tied to permission related issues or
    socket timeouts.

    It uses delivery confirmations and illustrates one way to keep track of
    messages that have been sent and if they've been confirmed by the broker.

    """
    _PUBLISH_INTERVAL = 0 # number of seconds to wait between publishing messages
    _WAIT_INTERVAL = 20   # number of seconds to wait before retrying connection


    def __init__(
        self,
        amqp_url,
        exchange,
        exchange_type,
        routing_key,
        max_messages,
        persistent
    ):
        """Setup the example publisher object, passing in the URL we will use
        to connect to the broker.

        :param str amqp_url: The URL for connecting to RabbitMQ
        :param str exchange_type: "direct" or "topic"
        :param str routing_key: The name of the routing key
        :param int max_messages: How many messages to send
        :param boo persistent: Whether to set messages to be persistent or not

        """
        self._connection = None
        self._channel = None
        self._deliveries = []
        self._acked = 0
        self._nacked = 0
        self._message_number = 0
        self._delivery_tag = 0
        self._stopping = False
        self._url = amqp_url
        self._exchange_type = exchange_type
        self._exchange = exchange
        self._routing_key = routing_key
        self._queue = routing_key
        self._max_messages = max_messages
        self._persistent = persistent
        self._closing = False
        self._create_exchange = True


    def connect(self):
        """This method connects to RabbitMQ, returning the connection handle.
        When the connection is established, the on_connection_open method
        will be invoked by pika. If you want the reconnection to work, make
        sure you set stop_ioloop_on_close to False, which is not the default
        behavior of this adapter.

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
        self._deliveries = []
        self._acked = 0
        self._nacked = 0
        self._delivery_tag = 0

        # This is the old connection IOLoop instance, stop its ioloop
        self._connection.ioloop.stop()

        # Create a new connection
        self._connection = self.connect()

        # There is now a new connection, needs a new ioloop to run
        self._connection.ioloop.start()


    def open_channel(self):
        """This method will open a new channel with RabbitMQ by issuing the
        Channel.Open RPC command. When RabbitMQ confirms the channel is open
        by sending the Channel.OpenOK RPC reply, the on_channel_open method
        will be invoked.

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
        self.setup_exchange(self._exchange)


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
        logging.warning('Channel was closed: (%s) %s', reply_code, reply_text)

        # if it's failing because it tried to declare an exchange but one already
        # existed with the same name but different parameters then continue
        if reply_code == 406:
            logging.debug("Exchange %s already exists", self._exchange)
            self._create_exchange=False
            self.open_channel()
        else:
            if not self._closing:
                self._connection.close()


    def setup_exchange(self, exchange_name):
        """Setup the exchange on RabbitMQ by invoking the Exchange.Declare RPC
        command. When it is complete, the on_exchange_declareok method will
        be invoked by pika.

        :param str|unicode exchange_name: The name of the exchange to declare

        """
        if self._create_exchange:
            logging.debug('Declaring exchange %s', exchange_name)
            self._channel.exchange_declare(
                callback=self.on_exchange_declareok,
                exchange=exchange_name,
                type=self._exchange_type,
                durable=True,
                passive=False)
        else:
            if self._exchange_type == "direct":
                self.setup_queue(self._queue)
            else:
                self.start_publishing()



    def on_exchange_declareok(self, unused_frame):
        """Invoked by pika when RabbitMQ has finished the Exchange.Declare RPC
        command.

        :param pika.Frame.Method unused_frame: Exchange.DeclareOk response frame

        """
        logging.debug('Exchange declared %s', unused_frame)

        # if it's a direct exchange, then create the queue
        # otherwise, it must be a pub/sub pattern so start publishing
        if self._exchange_type == "direct":
            self.setup_queue(self._queue)
        else:
            self.start_publishing()


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
                    self._exchange, self._queue, self._routing_key)
        self._channel.queue_bind(self.on_bindok, self._queue,
                                 self._exchange, self._routing_key)


    def on_bindok(self, unused_frame):
        """This method is invoked by pika when it receives the Queue.BindOk
        response from RabbitMQ. Since we know we're now setup and bound, it's
        time to start publishing."""
        logging.debug('Queue bound')
        self.start_publishing()


    def start_publishing(self):
        """This method will enable delivery confirmations and schedule the
        first message to be sent to RabbitMQ

        """
        logging.debug('Issuing consumer related RPC commands')
        self.enable_delivery_confirmations()
        self.schedule_next_message()


    def enable_delivery_confirmations(self):
        """Send the Confirm.Select RPC method to RabbitMQ to enable delivery
        confirmations on the channel. The only way to turn this off is to close
        the channel and create a new one.

        When the message is confirmed from RabbitMQ, the
        on_delivery_confirmation method will be invoked passing in a Basic.Ack
        or Basic.Nack method from RabbitMQ that will indicate which messages it
        is confirming or rejecting.

        """
        logging.debug('Issuing Confirm.Select RPC command')
        self._channel.confirm_delivery(self.on_delivery_confirmation)


    def on_delivery_confirmation(self, method_frame):
        """Invoked by pika when RabbitMQ responds to a Basic.Publish RPC
        command, passing in either a Basic.Ack or Basic.Nack frame with
        the delivery tag of the message that was published. The delivery tag
        is an integer counter indicating the message number that was sent
        on the channel via Basic.Publish. Here we're just doing house keeping
        to keep track of stats and remove message numbers that we expect
        a delivery confirmation of from the list used to keep track of messages
        that are pending confirmation.

        :param pika.frame.Method method_frame: Basic.Ack or Basic.Nack frame

        """
        confirmation_type = method_frame.method.NAME.split('.')[1].lower()
        logging.debug('Received %s for delivery tag: %i',
                    confirmation_type,
                    method_frame.method.delivery_tag)
        if confirmation_type == 'ack':
            self._acked += 1
        elif confirmation_type == 'nack':
            self._nacked += 1
        self._deliveries.remove(method_frame.method.delivery_tag)
        logging.debug('Published %i messages, %i have yet to be confirmed, '
                    '%i were acked and %i were nacked',
                    self._message_number, len(self._deliveries),
                    self._acked, self._nacked)


    def schedule_next_message(self):
        """If we are not closing our connection to RabbitMQ, schedule another
        message to be delivered in _PUBLISH_INTERVAL seconds.

        """
        if self._stopping:
            return

        logging.debug('Scheduling next message for %0.1f seconds',
                    self._PUBLISH_INTERVAL)
        self._connection.add_timeout(self._PUBLISH_INTERVAL,
                                     self.publish_message)


    def publish_message(self):
        """If the class is not stopping, publish a message to RabbitMQ,
        appending a list of deliveries with the message number that was sent.
        This list will be used to check for delivery confirmations in the
        on_delivery_confirmations method.

        Once the message has been sent, schedule another message to be sent.
        The main reason I put scheduling in was just so you can get a good idea
        of how the process is flowing by slowing down and speeding up the
        delivery intervals by changing the _PUBLISH_INTERVAL constant in the
        class.

        """
        if self._message_number == 0:
            self._first_message_time = datetime.datetime.now()

        if self._stopping:
            logging.debug("Script is stopping, cannot publish message")
            return

        if not self._connection.is_open:
            logging.debug("Connection is not open, cannot publish message")
            return

        message = {'sequence':(self._message_number+1)}
        message_id = uuid.uuid4()

        if self._persistent:
            properties = pika.BasicProperties(
                app_id=os.path.basename(__file__),
                content_type='application/json',
                delivery_mode=2, # make message persistent
                message_id=(str(message_id)),
                timestamp=int(time.time()))
        else:
            properties = pika.BasicProperties(
                app_id=os.path.basename(__file__),
                content_type='application/json',
                message_id=(str(message_id)),
                timestamp=int(time.time()))

        self._channel.basic_publish(self._exchange, self._routing_key,
                                    json.dumps(message, ensure_ascii=False),
                                    properties)
        self._message_number += 1
        self._delivery_tag += 1
        self._deliveries.append(self._delivery_tag)
        logging.debug('Published message # %i, tag %i, id %s',
                    self._message_number,
                    self._delivery_tag,
                    message_id)

        if self._message_number < self._max_messages:
            self.schedule_next_message()
        else:
            message_processing_time = datetime.datetime.now() - self._first_message_time
            logging.info("%s messages sent in %s (%s/s)",
                self._max_messages,
                message_processing_time,
                round(self._max_messages/message_processing_time.total_seconds(), 2))
            self.stop()


    def close_channel(self):
        """Invoke this command to close the channel with RabbitMQ by sending
        the Channel.Close RPC command.

        """
        logging.debug('Closing the channel')
        if self._channel:
            self._channel.close()


    def run(self):
        """Run the example code by connecting and then starting the IOLoop.

        """
        self._connection = self.connect()
        self._connection.ioloop.start()


    def stop(self):
        """Stop the example by closing the channel and connection. We
        set a flag here so that we stop scheduling new messages to be
        published. The IOLoop is started because this method is
        invoked by the Try/Catch below when KeyboardInterrupt is caught.
        Starting the IOLoop again will allow the publisher to cleanly
        disconnect from RabbitMQ.

        """
        logging.info('Stopping')
        self._stopping = True
        self.close_channel()
        self.close_connection()
        self._connection.ioloop.start()
        logging.debug('Stopped')


    def close_connection(self):
        """This method closes the connection to RabbitMQ."""
        logging.debug('Closing connection')
        self._closing = True
        self._connection.close()


# --- START OF MAIN ----------------------------------------------------------

def main():
    start_time = datetime.datetime.now()
    (broker, routing_key, exchange, exchange_type, max_messages, persistent, log_level) = process_options()

    logging.basicConfig(
            level=log_level,
            format='[%(levelname)s] (%(threadName)-10s) %(message)s',
        )
    logging.debug(datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p") + " Started")

    conn = Publisher(
        broker,
        exchange,
        exchange_type,
        routing_key,
        max_messages,
        persistent
    )

    if max_messages > 0:
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
    main()
