# Python ActiveMQ

I needed to set up an environment wherein I could demonstrate and investigate ActiveMQ, AMQP, clustering, failover, etc.

I chose to do this in Python, as I was working with some developers who were having trouble connecting to the message bus and so wanted a working example.

One of these scripts will relentlessly publish messages (within which is a sequence number) to a topic.  The other will subscribe to the topic and report if the sequence goes awry (NB FIFO is not necessarily expected but all messages being delivered is).

The intent is run the scripts across an ActiveMQ cluster and then try to shoot various elements of it down to see how it fails.

## ActiveMQ configuration

In the `resources` folder is a configuration file for an ActiveMQ broker.  The idea is that you spin up multiple machines with this configuration and they will cluster themselves.

### Pre-requisites

- ActiveMQ 5.14.3
- A file server with a network share that is...
  1. Available over NFS
  1. Mounted on the ActiveMQ servers as /mnt/nfs-share
- Python 3.4 running on your local machine with access to the ActiveMQ servers on port 5672
  - Alternatively, you can run the scripts directly on the ActiveMQ servers
- HA Proxy load balancer
  - A configuration file for this is also provided (NB contains IP addresses, so may need adjusting for your environment)

## Calling syntax

The Python scripts will provide usage information id run with a `-h` flag.

### Producer

Publish one hundred non-persistent messages to a topic (broker on localhost:5672)

    python3 message_producer.py -t topic_name -m 100 -v

Publish one hundred persistent messages to a queue on a remote machine

    python3 message_producer.py -b 127.0.1.2:5672 -q queue_name -m 100 -vp

### Receiver

Listen for 100 messages on a topic (broker on localhost:5672)

    python3 message_receiver.py -t topic_name -m 100 -v

Listen indefinitely to a queue (broker on localhost:5672)

    python3 message_receiver.py -q queue_name -m 0 -v
