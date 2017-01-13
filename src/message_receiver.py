'''
Created on 13th Jan 2017

@author: Jeremy Gooch

    Python AMQP message receiver.

    Execute script with -h parameter for usage
'''

# --- LIBRARIES --------------------------------------------------------------

import argparse
import datetime
import sys
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
                      required=True,
                      default="localhost:5672/examples",
                      help="connection string and queue name, separated by '/'")
    opts.add_argument("--max_messages", "-m",
                      type=int,
                      default=100,
                      required=True,
                      help="number of messages to receive before stopping (default %default). Setting '0' retrieves indefinitely")
    opts.add_argument("--verbose", "-v",
                      required=False,
                      default=False,
                      action="store_true",
                      help="send log messages to sysout")
    options = opts.parse_args()

    # Check that the connection string looks sensible
    checkConnection = re.match('(.*):\d{1,5}\/(.*)', options.broker, )
    if not(checkConnection):
        opts.error("The broker connection string looks a bit dodgy.  It should be something like 'localhost:5672/example'")
    
    return(options.broker, options.max_messages, options.verbose)


# --- CLASSES ----------------------------------------------------------------

class Recv(MessagingHandler):
    def __init__(self, url, count, logger):
        super(Recv, self).__init__()
        self.url = url
        self.expected = count
        self.received = 0
        self.logger = logger


    def on_start(self, event):
        event.container.create_receiver(self.url)
        self.logger.log("Connected to " + self.url)


    def on_message(self, event):
        if event.message.id and event.message.id < self.received:
            # ignore duplicate message
            self.logger.log("Duplicate message received " + str(event.message.body))
            return
        
        if self.expected == 0 or self.received < self.expected:
            print(event.message.body)
            self.received += 1
            if self.received == self.expected:
                event.receiver.close()
                event.connection.close()
                self.logger.log(str(self.received) + " messages received")
                self.logger.log("Disconnected from " + self.url)


class script_logger(object):
    def __init__(self, log_flag):
        '''
        Script control class for logging messages (if required) and stopping execution
        '''
        
        self.log_flag = log_flag


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
        self.log("Exiting with return code " + str(exit_code))
        sys.exit(exit_code)


    
# --- START OF MAIN ----------------------------------------------------------

def main():
    (broker, max_messages, log_flag) = process_options()
    
    logger = script_logger(log_flag)
    logger.log("Started")

    try:
        Container(Recv(broker, max_messages, logger)).run()
    except KeyboardInterrupt: pass
    
    logger.stop("Finished", 0, False)



# --- END OF MAIN ------------------------------------------------------------


if __name__ == "__main__":
    main()