# AMQP Python Go

I needed to set up an environment wherein I could demonstrate and investigate ActiveMQ, RabbitMQ, AMQP, clustering, failover, etc and connect from clients written in both Python and Go.

For each of the two languages, there are two programs that use the AMQP 1.0 protocol to connect.  One will publish lots of messages to a topic or a queue.  The other will subscribe to the topic or connect to the queue and pull the messages down.  The subscription can be durable (so that messages sent when off-line are kept for future delivery) or ephemeral.

There are also other programs, such as [Python Pika](https://pika.readthedocs.io/en/0.10.0/) clients, which connect over AMQP 0-9-1.

## Calling syntax

All of the Python scripts will provide usage information id run with a `-h` flag.

## Docker

Also provided are Dockerfiles for a standalone ActiveMQ or RabbitMQ service and the client scripts.  The latter include the installation of the necessary [qpid-proton](https://qpid.apache.org/proton/index.html) and [qpid-electron](https://godoc.org/qpid.apache.org/electron) libraries.

The Docker Compose services for the RabbitMQ and ActiveMQ brokers may be executed as follows.  Note that they have overlapping ports, as it's not intended here to run them side-by-side.

### ActiveMQ

From the project root folder...

    docker-compose up --build activemq

This will create and run a container called `activemq_1`.

### RabbitMQ

From the project root folder...

    docker-compose up --build rabbitmq

This will create and run a container called `rabbitmq_1`.

### ssl-gen

This module creates a set of self-signed client and server certificates and keys, placing them into a reusable Docker volume.

The RabbitMQ Docker Compose service and the Python Pika scripts use this to provide example code for encryption and client authentication.

The service can be called independently, if desired.  It will start up, generate the keys and certs, and a volume to hold them, and then shut down.

    docker-compose up --build ssl-gen
