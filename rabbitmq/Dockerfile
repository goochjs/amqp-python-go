FROM rabbitmq:3-management
ARG SSL_PASSWORD

USER root
RUN apt-get update

# install the RabbitMQ admin tool (which is a Python script)
RUN apt-get install -y python
ADD https://raw.githubusercontent.com/rabbitmq/rabbitmq-management/rabbitmq_v3_6_10/bin/rabbitmqadmin /usr/local/bin/rabbitmqadmin
RUN chmod 755 /usr/local/bin/rabbitmqadmin

# Bring in our configuration
COPY rabbitmq.config /etc/rabbitmq/rabbitmq.config
RUN chown rabbitmq:rabbitmq /etc/rabbitmq/rabbitmq.config && chmod 644 /etc/rabbitmq/rabbitmq.config

# set up SSL
RUN apt-get install openssl -y  \
	&& mkdir -p /home/ssl/ca/certs \
	&& mkdir -p /home/ssl/ca/private \
	&& chmod 700 /home/ssl/ca/private \
	&& echo 01 > /home/ssl/ca/serial \
	&& touch /home/ssl/ca/index.txt \
    && mkdir -p /home/ssl/server \
	&& mkdir -p /home/ssl/client

COPY openssl.cnf /home/ssl/ca

# Prepare the certificate authority (self-signed)
# Create a self-signed certificate that will serve a certificate authority (CA)
# The private key is located under "private"
# Generate a certificate from our private key
# Sign the certificate with our CA
RUN cd /home/ssl/ca \
    && openssl req -x509 -config openssl.cnf -newkey rsa:2048 -days 365 -out cacert.pem -outform PEM -subj /CN=MyTestCA/ -nodes \
    && openssl x509 -in cacert.pem -out cacert.cer -outform DER \
    && cd /home/ssl/server \
    && openssl genrsa -out key.pem 2048 \
    && openssl req -new -key key.pem -out req.pem -outform PEM -subj /CN=rabbitmq/O=server/ -nodes \
    && cd /home/ssl/ca \
    && openssl ca -config openssl.cnf -in /home/ssl/server/req.pem -out /home/ssl/server/cert.pem -notext -batch -extensions server_ca_extensions \
    && cd /home/ssl/server \
    && openssl pkcs12 -export -out keycert.p12 -in cert.pem -inkey key.pem -passout pass:$SSL_PASSWORD

# Generate a private RSA key
# Generate a certificate from our private key
# Sign the certificate with our CA
# Create a key store that will contain our certificate
# Create a trust store that will contain the certificate of our CA
RUN cd /home/ssl/client \
    && openssl genrsa -out key.pem 2048 \
    && openssl req -new -key key.pem -out req.pem -outform PEM -subj /CN=rabbitmq/O=client/ -nodes \
    && cd /home/ssl/ca \
    && openssl ca -config openssl.cnf -in /home/ssl/client/req.pem -out /home/ssl/client/cert.pem -notext -batch -extensions client_ca_extensions \
    && cd /home/ssl/client \
    && openssl pkcs12 -export -out key-store.p12 -in cert.pem -inkey key.pem -passout pass:$SSL_PASSWORD \
    && openssl pkcs12 -export -out trust-store.p12 -in /home/ssl/ca/cacert.pem -inkey /home/ssl/ca/private/cakey.pem -passout pass:$SSL_PASSWORD

USER rabbitmq

# Load plug-ins
RUN rabbitmq-plugins enable --offline rabbitmq_shovel \
    && rabbitmq-plugins enable --offline rabbitmq_shovel_management \
    && rabbitmq-plugins enable rabbitmq_auth_mechanism_ssl
