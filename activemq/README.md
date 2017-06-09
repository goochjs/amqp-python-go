# ActiveMQ

## ActiveMQ configuration

In the `activemq` folder is a configuration file for an ActiveMQ broker.  The idea is that you spin up multiple machines with this configuration and they will cluster themselves.

### Pre-requisites

- ActiveMQ 5.14.3
- A file server with a network share that is...
  1. Available over NFS
  1. Mounted on the ActiveMQ servers as /mnt/nfs-share
- Python 3.4 running on your local machine with access to the ActiveMQ servers on port 5672
  - Alternatively, you can run the scripts directly on the ActiveMQ servers
- HA Proxy load balancer
  - A configuration file for this is provided in the `haproxy` folder (NB contains IP addresses, so may need adjusting for your environment)

## Docker

From the project root folder...

    docker-compose up --build activemq

This will create and run a container called `activemq_1`.
