Python ActiveMQ
===============

I needed to set up an environment wherein I could demonstrate and investigate ActiveMQ, AMQP, clustering, failover, etc.

I chose to do this in Python, as I was working with some developers who were having trouble connecting to the message bus and so wanted a working example.

One of these scripts will relentlessly publish messages (within which is a sequence number) to a topic.  The other will subscribe to the topic and report if the sequence goes awry (NB FIFO is not necessarily expected but all messages being delivered is).

The intent is run the scripts across an ActiveMQ cluster and then try to shoot various elements of it down to see how it fails.
