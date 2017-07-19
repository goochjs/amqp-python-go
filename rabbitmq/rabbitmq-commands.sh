#!/bin/bash

# Example command line syntax

# create policy
rabbitmqctl set_policy DLX ".*" '{"dead-letter-exchange":"DLX"}' --apply-to queues

# import definitions
rabbitmqadmin -u admin -p password -q import /mnt/rabbitmq/config/rabbitmq-defs.json
