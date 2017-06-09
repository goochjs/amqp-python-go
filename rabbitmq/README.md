# RabbitMQ

## Dockerised RabbitMQ

    docker run -d --hostname my-rabbit --name rabbitmq_1 -p 8080:15672 -p 5672:5672 rabbitmq:3-management

    docker build -t rabbitmq-amqp -f ./Dockerfile-RabbitMQ .

    docker run -d --hostname my-rabbit --name rabbitmq_1 -p 8080:15672 -p 5672:5672 rabbitmq-amqp

## Management portal

    http://localhost:8080

## Bash shell with network access to Rabbit

    docker run -it --network container:rabbitmq_1 bash

    docker build -t python-rabbitmq-producer -f ./Dockerfile-producer .

    docker run -it --rm --name python-rabbitmq-producer_1 --network container:rabbitmq_1 python-rabbitmq-producer -b user:password@localhost:5672 -t some_topic -m 10 -vp
