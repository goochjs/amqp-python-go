#!/usr/bin/python3
'''
Created on 14th July 2017

@author: Jeremy Gooch

    Generates a salted SHA-256 hash of an incoming string,
    conformant to RabbitMQ's password hash computation
    https://www.rabbitmq.com/passwords.html

    Execute script with -h parameter for usage
'''

# --- LIBRARIES --------------------------------------------------------------

import sys
if sys.version_info[0] < 3:
    raise Exception("Python 3 or a more recent version is required.")

import argparse
import logging

import os
import binascii
import hashlib
import base64


# --- CONSTANTS --------------------------------------------------------------
SALT_LENGTH=4


# --- FUNCTIONS --------------------------------------------------------------

def process_options():
    '''
    Processes command line options
    '''

    opts = argparse.ArgumentParser(description="Generates a salted SHA-256 hash of an incoming string.")

    opts.add_argument("input_string",
        nargs="?",
        help="input string")
    opts.add_argument("-v", "--verbose",
        required=False,
        default=False,
        action="store_true",
        help="send log messages to sysout")
    options = opts.parse_args()

    if options.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    return(
        options.input_string,
        log_level)


def hextrim(binary_thing):
    # extract just the hex bit of a binary representation
    # TODO - there must be a neater way to do this bit!
    hex_end=len(str(binary_thing))-1
    return str(binary_thing)[2:hex_end]


# --- START OF MAIN ----------------------------------------------------------

def main():
    (input_string, log_level) = process_options()

    logging.basicConfig(
            level=log_level,
            format='[%(levelname)s] (%(threadName)-10s) %(message)s',
        )

    # generate a random hexadecimal salt
    salt = binascii.hexlify(os.urandom(SALT_LENGTH))

    # concatenate the salt and the input string and hash the result
    hashed_salted_output = hashlib.sha256(salt + input_string.encode())

    # concatenate the hex salt again and base64 encode it all
    encoded_output = base64.b64encode((str(hextrim(salt)) + hashed_salted_output.hexdigest()).encode())

    logging.debug("Input string - %s", input_string)
    logging.debug("Salt - %s", salt)
    logging.debug("Hashed and salted output - %s", hashed_salted_output.hexdigest())

    print(hextrim(encoded_output))


# --- END OF MAIN ------------------------------------------------------------


if __name__ == "__main__":
    main()
