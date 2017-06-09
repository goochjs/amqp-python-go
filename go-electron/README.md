# go-electron clients

The Go clients are run from within a bash shell.  From within the `go-electron` folder...

    docker build -t go-electron .

To run the Go clients, connecting to an ActiveMQ running within a container called `activemq_1`, first of all start the container...

    docker run --rm -it -d --name go-electron_1 -v ${PWD}:/usr/src/go-electron --network container:activemq_1 go-electron bash

Then connect to it and run either the Receiver or the Sender, as per the commands below.

#### Receiver

    docker exec -it go-electron_1 bash
    go run receive.go -debug -name go-client -source topic://some_topic -count 10 amqp://localhost:5672

#### Sender

    docker exec -it go-electron_1 bash
    go run send.go -debug -count 10 -dest topic://some_topic localhost:5672
