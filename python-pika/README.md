# Python Pika clients

## Docker

    docker build -t pika-producer -f ./Dockerfile-producer .

    docker run -it --rm --name pika-producer_1 --network container:rabbitmq_1 pika-producer -b user:user@localhost:5672 -q some_queue -m 3 -vp
