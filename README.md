# Python ActiveMQ

I needed to set up an environment wherein I could demonstrate and investigate ActiveMQ, AMQP, clustering, failover, etc.

I chose to do this in Python, as I was working with some developers who were having trouble connecting to the message bus and so wanted a working example.

One of these scripts will relentlessly publish messages (within which is a sequence number) to a topic.  The other will subscribe to the topic and report if the sequence goes awry (NB FIFO is not necessarily expected but all messages being delivered is).

The intent is run the scripts across an ActiveMQ cluster and then try to shoot various elements of it down to see how it fails.

## ActiveMQ configuration

In the `resources` folder is a configuration file for an ActiveMQ broker.  The idea is that you spin up multiple machines with this configuration and they will cluster themselves.

### Pre-requisites

- ActiveMQ 5.14.3
- A file server with a network share that is...
  1. Available over NFS
  1. Mounted on the ActiveMQ servers as /mnt/nfs-share
- Python 3.4 running on your local machine with access to the ActiveMQ servers on port 5672
  - Alternatively, you can run the scripts directly on the ActiveMQ servers
- **ACCESS BETWEEN ActiveMQ SERVERS??**
