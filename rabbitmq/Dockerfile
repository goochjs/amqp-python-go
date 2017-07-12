FROM rabbitmq:3-management

#USER root

# Create the directories for the persistence and log stores
#RUN mkdir -p /data/rabbitmq && \
#    chown rabbitmq:rabbitmq /data/rabbitmq
#RUN mkdir -p /data/mnesia && \
#    chown rabbitmq:rabbitmq /data/mnesia
#RUN mkdir -p /data/log && \
#    chown rabbitmq:rabbitmq /data/log

# Copy config to the container
#COPY ./rabbitmq.config /data/rabbitmq/config/rabbitmq.config
#COPY ./rabbitmq-defs.json /data/rabbitmq/config/rabbitmq-defs.json
#RUN chown -R rabbitmq:rabbitmq /data/rabbitmq/config
#RUN chmod -R 644 /data/rabbitmq/config

#USER rabbitmq

# Load plug-ins
#RUN rabbitmq-plugins enable rabbitmq_amqp1_0
