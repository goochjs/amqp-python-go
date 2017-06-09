# Python Proton clients

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

### python-message-receiver

From the Python script folder...

    docker build -t python-message-receiver -f ./Dockerfile-receiver .

If connecting to ActiveMQ running natively on your localhost...

    docker run -it --rm --name python-message-receiver_1 python-message-receiver -q some_queue -m 100 -v

If connecting to ActiveMQ running in a Docker container called `activemq_1` (requiring an ID and password)...

    docker run -it --rm --name python-message-receiver_1 --network container:activemq_1 python-message-receiver -b user:password@localhost:5672 -t some_topic -m 0 -v -n python-client

If connecting to ActiveMQ running somewhere else...

    docker run -it --rm --name python-message-receiver_1 python-message-receiver -b 127.0.1.2:5672 -t some_topic -m 100 -v

### python-message-producer

Similarly for the `message_producer`...

    docker build -t python-message-producer -f ./Dockerfile-producer .

    docker run -it --rm --name python-message-producer_1 --network container:activemq_1 python-message-producer -b user:password@localhost:5672 -t some_topic -m 10 -vp

..etc etc

### File sender

Another script offers the ability to send a file into ActiveMQ, one line at a time.  Example calling syntax to send the content of the script file itself into ActiveMQ...

    docker build -t python-file_sender -f ./Dockerfile-sender .

    docker run -it --rm --name python-file-sender_1 --network container:activemq_1 python-file-sender -b user:password@localhost:5672 -t some_topic -f /usr/src/python-proton/file_sender.py -a header1=something -a header2=somethingelse
