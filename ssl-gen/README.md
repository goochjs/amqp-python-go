# ssl-gen

Creates a set of self-signed certificates and keys for SSL testing.

The following variables may be overwritten with environment variables

- ${SSL_CFG} - location of openssl config file
- ${SSL_PASSWORD} - password to be used when creating keys
- ${SERVER_SUBJ} - subject (common name, org, etc) to be assigned to server cert
- ${CLIENT_SUBJ} - subject (common name, org, etc) to be assigned to client key
- ${CA_SUBJ} - subject (common name, org, etc) to be assigned to CA cert
- ${SSL_DIR} - root directory of all keys and certs
- ${SSL_CA_DIR} - specific directory for CA certs
- ${SSL_SERVER_DIR} - specific directory for server certs
- ${SSL_CLIENT_DIR} - specific directory for client keys
- ${SSL_PRIVATE_DIR} - specific directory for CA private key


## Docker

From the ssl-gen directory

    docker build -t ssl-gen -f ./Dockerfile .
    docker run -v certs:/mnt/ssl ssl-gen


# Docker Compose

From the project root folder...

    docker-compose up --build ssl-gen

This will create a volume ("ssl-vol") with CA, server and client certs and keys for use in other containers.
