# AMQP ActiveMQ Python Go

I needed to set up an environment wherein I could demonstrate and investigate ActiveMQ, AMQP, clustering, failover, etc and connect from clients written in both Python and Go.

For each of the two languages, there are two programs.  One will publish lots of messages to a topic or a queue.  The other will subscribe to the topic or connect to the queue and pull the messages down.  The subscription can be durable (so that messages sent when off-line are kept for future delivery) or ephemeral.

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

    python3 message_producer.py -t some_topic -m 100 -v

Publish one hundred persistent messages to a queue where the broker (or load balancer) is on a remote machine

    python3 message_producer.py -b 127.0.1.2:5672 -q some_queue -m 100 -vp

### Receiver

Listen for 100 messages on a topic (via localhost:5672)

    python3 message_receiver.py -t some_topic -m 100 -v

Listen indefinitely to a queue (via localhost:5672)

    python3 message_receiver.py -q some_queue -m 0 -v

## Docker

Also provided are Dockerfiles for a standalone ActiveMQ service and the client scripts.  The latter include the installation of the necessary [qpid-proton](https://qpid.apache.org/proton/index.html) and [qpid-electron](https://godoc.org/qpid.apache.org/electron) lbraries.

### ActiveMQ

From the project root directory...

    docker-compose up activemq

This will create and run a container called `activemq_1`.

### python-message-receiver

From the Python script directory...

    docker build -t python-message-receiver -f ./Dockerfile-receiver .

If connecting to ActiveMQ running natively on your localhost...

    docker run -it --rm --name python-message-receiver_1 python-message-receiver -q some_queue -m 100 -v

If connecting to ActiveMQ running in a Docker container called `activemq_1`...

    docker run -it --rm --name python-message-receiver_1 --network container:activemq_1 python-message-receiver -q some_queue -m 0 -v -n python-message-receiver-client

If connecting to ActiveMQ running somewhere else...

    docker run -it --rm --name python-message-receiver_1 python-message-receiver -b 127.0.1.2:5672 -t some_topic -m 100 -v

### python-message-producer

Similarly for the `message_producer`...

    docker build -t python-message-producer -f ./Dockerfile-producer .

    docker run -it --rm --name python-message-producer_1 --network container:activemq_1 python-message-producer -t some_topic -m 10 -vp

..etc etc

### go-electron

The Go clients are run from within a bash shell.  From within the `go-electron` directory...

    docker build -t go-electron .

To run the Go clients, connecting to an ActiveMQ running within a container called `activemq_1`...

    docker run --rm -it -d --name go-electron_1 -v ${PWD}:/usr/src/go-electron --network container:activemq_1 go-electron bash
    docker exec -it go-electron_1 bash
    go run send.go
    go run receive.go
