# Python ActiveMQ

I needed to set up an environment wherein I could demonstrate and investigate ActiveMQ, AMQP, clustering, failover, etc.

I chose to do this in Python, as I was working with some developers who were having trouble connecting to the message bus and so wanted a working example.

One of these scripts will  publish lots of messages (within each of which is a sequence number) to a topic or a queue.  The other will subscribe to the topic or connect to the queue and pull the messages down.  The subscription can be durable or ephemeral.

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

Publish one hundred non-persistent messages to a topic (broker or load balancer available on localhost:5672)

    python3 message_producer.py -t topic_name -m 100 -v

Publish one hundred persistent messages to a queue where the broker or load balancer is on a remote machine

    python3 message_producer.py -b 127.0.1.2:5672 -q queue_name -m 100 -vp

### Receiver

Listen for 100 messages on a topic (via localhost:5672)

    python3 message_receiver.py -t topic_name -m 100 -v

Listen indefinitely to a queue (via localhost:5672)

    python3 message_receiver.py -q queue_name -m 0 -v

## Docker

Also provided are Dockerfiles for the client scripts.  These include the installation of the necessary qpid-proton lbraries.

### Receiver

From the Python script directory...

    docker build -t python-message-receiver -f ./Dockerfile-receiver .

If connecting to ActiveMQ running natively on your localhost...

    docker run -it --rm --name python-message-receiver_1 python-message-receiver -q queue_name -m 100 -v

If connecting to ActiveMQ running in a different Docker container on your localhost then (NB change `PUT_NAME_HERE` as appropriate)...

    docker run -it --rm --name python-message-receiver_1 --network container:PUT_NAME_HERE python-message-receiver -q some_queue -m 0 -v

If connecting to ActiveMQ running somewhere else...

    docker run -it --rm --name python-message-receiver_1 python-message-receiver -b 127.0.1.2:5672 -q queue_name -m 100 -v

### Producer

Similarly for the `message_producer`...

    docker build -t python-message-producer -f ./Dockerfile-producer .

    docker run -it --rm --name python-message-producer_1 --network container:PUT_NAME_HERE python-message-producer -q queue_name -m 10

..etc etc
