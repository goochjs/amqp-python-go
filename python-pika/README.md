# Python Pika clients

## Docker

    docker build -t python-rabbitmq-producer -f ./Dockerfile-producer .

    docker run -it --rm --name python-rabbitmq-producer_1 --network container:rabbitmq_1 python-rabbitmq-producer
