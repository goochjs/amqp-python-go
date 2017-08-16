FROM rabbitmq:3.6.6

USER root
RUN apt-get update

# install the RabbitMQ admin tool (which is a Python script)
RUN apt-get install -y python
ADD https://raw.githubusercontent.com/rabbitmq/rabbitmq-management/rabbitmq_v3_6_10/bin/rabbitmqadmin /usr/local/bin/rabbitmqadmin
RUN chmod 755 /usr/local/bin/rabbitmqadmin

# Bring in our RabbitMQ configuration file
COPY rabbitmq.config /etc/rabbitmq/rabbitmq.config
RUN chown rabbitmq:rabbitmq /etc/rabbitmq/rabbitmq.config && chmod 444 /etc/rabbitmq/rabbitmq.config

# initialise the transaction log directory
RUN mkdir -p /mnt/rabbitmq/data/mnesia && chown rabbitmq:rabbitmq /mnt/rabbitmq/data/mnesia

USER rabbitmq

# Load plug-ins
RUN rabbitmq-plugins enable --offline rabbitmq_management \
    && rabbitmq-plugins enable --offline rabbitmq_shovel \
    && rabbitmq-plugins enable --offline rabbitmq_shovel_management \
    && rabbitmq-plugins enable --offline rabbitmq_auth_mechanism_ssl

# Launch the message broker
CMD rabbitmq-server
