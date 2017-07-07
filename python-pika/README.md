# Python Pika clients

AMQP 0-9-1 has a more complicated messaging model than AMQP 1.0.  Messages are sent to exchanges, from where a combination of a producer-supplied routing key and a consumer-supplied binding key will dictate to which queue they are sent.

These scripts assume that producers are responsible for defining exchanges.  If a *direct* exchange is used, then the producer will also declare the queue.  Otherwise, where *topics* are used, it is the consumer's responsibility to define the queue.


## pika_producer

This client will connect to a broker and declare an exchange.  If a queue has been requested in the parameters, then it will also declare the queue and start to send messages.  If a topic is declared, then it will not create the queue but will begin to send messages.  The exchange, queue and routing key will all be given the same name.

    python3 pika_producer.py -b user:user@localhost:5672 -q some.queue -m 10 -vp


## pika_receiver

This client will connect to a broker and attempt to connect to an exchange.  Once connected, it will declare a queue (if not already in existence) and connect to it using a binding key of the same name (NB it expects the exchange to have the same name also).  It will then start to consume messages.

    python pika_receiver.py -b user:user@localhost:5672 -q some.queue -m 10 -v


## Docker

    docker build -t pika-producer -f ./Dockerfile-producer .

    docker build -t pika-receiver -f ./Dockerfile-receiver .

    docker run -it --rm --name pika-producer_1 --network container:rabbitmq_1 pika-producer -b user:user@localhost:5672 -q some.queue -m 10 -vp

    docker run -it --rm --name pika-receiver_1 --network container:rabbitmq_1 pika-receiver -b user:user@localhost:5672 -q some.queue -m 0 -v
