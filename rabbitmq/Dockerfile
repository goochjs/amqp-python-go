FROM rabbitmq:3-management

# install the admin tool (which is a Python script)
RUN apt-get update
RUN apt-get install -y python
ADD https://raw.githubusercontent.com/rabbitmq/rabbitmq-management/rabbitmq_v3_6_10/bin/rabbitmqadmin /usr/local/bin/rabbitmqadmin
RUN chmod 755 /usr/local/bin/rabbitmqadmin

# import the definitions
#CMD /usr/local/bin/rabbitmqadmin -u user -p user -q import /mnt/rabbitmq/config/rabbitmq-defs.json

# Load plug-ins
#RUN rabbitmq-plugins enable rabbitmq_amqp1_0
RUN rabbitmq-plugins enable --offline rabbitmq_shovel && rabbitmq-plugins enable --offline rabbitmq_shovel_management
