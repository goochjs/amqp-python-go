#!/bin/bash

# Example command line syntax

# create policy
rabbitmqctl set_policy DLX ".*" '{"dead-letter-exchange":"DLX"}' --apply-to queues

# import definitions
rabbitmqadmin -u user -p user -q import /mnt/rabbitmq/config/rabbitmq-defs.json
