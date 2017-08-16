#!/bin/sh

# the following may be overwritten with environment variables
[[ -z ${SSL_CFG} ]] && SSL_CFG="/usr/src/ssl/openssl.cnf"
[[ -z ${SSL_PASSWORD} ]] && SSL_PASSWORD="itsasecret"
[[ -z ${SERVER_SUBJ} ]] && SERVER_SUBJ="/CN=server/O=server/"
[[ -z ${CLIENT_SUBJ} ]] && CLIENT_SUBJ="/CN=client/O=client/"
[[ -z ${CA_SUBJ} ]] && CA_SUBJ="/CN=ssl-gen_CA/"
[[ -z ${SSL_DIR} ]] && SSL_DIR="/mnt/ssl"
[[ -z ${SSL_CA_DIR} ]] && SSL_CA_DIR="${SSL_DIR}/ca"
[[ -z ${SSL_SERVER_DIR} ]] && SSL_SERVER_DIR="${SSL_DIR}/server"
[[ -z ${SSL_CLIENT_DIR} ]] && SSL_CLIENT_DIR="${SSL_DIR}/client"
[[ -z ${SSL_PRIVATE_DIR} ]] && SSL_PRIVATE_DIR="${SSL_CA_DIR}/private"


# create directories that don't exist
[[ ! -d ${SSL_DIR} ]] && mkdir -p ${SSL_DIR}
[[ ! -d ${SSL_CA_DIR} ]] && mkdir -p ${SSL_CA_DIR}/certs
[[ ! -d ${SSL_SERVER_DIR} ]] && mkdir -p ${SSL_SERVER_DIR}
[[ ! -d ${SSL_CLIENT_DIR} ]] && mkdir -p ${SSL_CLIENT_DIR}
[[ ! -d ${SSL_PRIVATE_DIR} ]] && mkdir -p ${SSL_PRIVATE_DIR} && chmod 700 ${SSL_PRIVATE_DIR}


# blow up if the SSL config file doesn't exist
[[ ! -f ${SSL_CFG} ]] && echo "SSL config file not found ${SSL_CFG}" && exit 9


# initialise some stuff
[[ ! -f ${SSL_CA_DIR}/serial ]] && echo 01 > ${SSL_CA_DIR}/serial
[[ ! -f ${SSL_CA_DIR}/index.txt ]] && touch ${SSL_CA_DIR}/index.txt


# Prepare the certificate authority (self-signed)
# Create a self-signed certificate that will serve a certificate authority (CA)
# The private key is located under "private"
# Generate a certificate from our private key
# Sign the certificate with our CA
cd ${SSL_CA_DIR} \
    && openssl req -x509 -config $SSL_CFG -newkey rsa:2048 -days 365 -out cacert.pem -outform PEM -subj $CA_SUBJ -nodes \
    && openssl x509 -in cacert.pem -out cacert.cer -outform DER \
    && cd ${SSL_SERVER_DIR} \
    && openssl genrsa -out key.pem 2048 \
    && openssl req -new -key key.pem -out req.pem -outform PEM -subj ${SERVER_SUBJ} -nodes \
    && cd ${SSL_CA_DIR} \
    && openssl ca -config $SSL_CFG -in ${SSL_SERVER_DIR}/req.pem -out ${SSL_SERVER_DIR}/cert.pem -notext -batch -extensions server_ca_extensions \
    && cd ${SSL_SERVER_DIR} \
    && openssl pkcs12 -export -out keycert.p12 -in cert.pem -inkey key.pem -passout pass:${SSL_PASSWORD}

# Generate a private RSA key
# Generate a certificate from our private key
# Sign the certificate with our CA
# Create a key store that will contain our certificate
# Create a trust store that will contain the certificate of our CA
cd ${SSL_CLIENT_DIR} \
    && openssl genrsa -out key.pem 2048 \
    && openssl req -new -key key.pem -out req.pem -outform PEM -subj ${CLIENT_SUBJ} -nodes \
    && cd ${SSL_CA_DIR} \
    && openssl ca -config $SSL_CFG -in ${SSL_CLIENT_DIR}/req.pem -out ${SSL_CLIENT_DIR}/cert.pem -notext -batch -extensions client_ca_extensions \
    && cd ${SSL_CLIENT_DIR} \
    && openssl pkcs12 -export -out key-store.p12 -in cert.pem -inkey key.pem -passout pass:${SSL_PASSWORD} \
    && openssl pkcs12 -export -out trust-store.p12 -in ${SSL_CA_DIR}/cacert.pem -inkey ${SSL_PRIVATE_DIR}/cakey.pem -passout pass:${SSL_PASSWORD}
