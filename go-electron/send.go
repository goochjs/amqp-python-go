package main

import (
	"fmt"
	"log"
	"os"
	"sync"

	"qpid.apache.org/amqp"
	"qpid.apache.org/electron"
)

const amqpResourceName = "some_topic"
const numberOfMessages = 10

var wait sync.WaitGroup
var container electron.Container
var connections chan electron.Connection
var sentChan chan electron.Outcome

func debugf(format string, data ...interface{}) {
	log.Printf(format, data...)
}

func main() {
	urlStr := "amqp://localhost:5672"

	sentChan = make(chan electron.Outcome) // Channel to receive acknowledgements.

	wait.Add(1) // Wait for one goroutine per URL.

	container = electron.NewContainer(fmt.Sprintf("send[%v]", os.Getpid()))
	connections = make(chan electron.Connection, 1) // Connections to close on exit

	// Start a goroutine
	debugf("Connecting to %v\n", urlStr)
	go produce(urlStr)

	// Wait for all the acknowledgements
	expect := int(numberOfMessages)
	debugf("Started senders, expect %v acknowledgements\n", expect)
	for i := 0; i < expect; i++ {
		out := <-sentChan // Outcome of async sends.
		if out.Error != nil {
			log.Fatalf("acknowledgement[%v] %v error: %v\n", i, out.Value, out.Error)
		} else {
			debugf("acknowledgement[%v]  %v (%v)\n", i, out.Value, out.Status)
		}
	}
	fmt.Printf("Received all %v acknowledgements\n", expect)

	wait.Wait() // Wait for all goroutines to finish.
	close(connections)
	for c := range connections { // Close all connections
		if c != nil {
			c.Close(nil)
		}
	}
}

func produce(urlStr string) {
	defer wait.Done() // Notify main() when this goroutine is done.
	var err error
	if url, err := amqp.ParseURL(urlStr); err == nil {
		if c, err := container.Dial("tcp", url.Host); err == nil {
			connections <- c // Save connection so we can Close() when main() ends
			if s, err := c.Sender(electron.Target("topic://" + amqpResourceName)); err == nil {
				// Loop sending messages.
				for i := int64(0); i < numberOfMessages; i++ {
					m := amqp.NewMessage()
					body := fmt.Sprintf("%v%v", url.Path, i)
					m.Marshal(body)
					s.SendAsync(m, sentChan, body) // Outcome will be sent to sentChan
				}
			}
		}
	}
	if err != nil {
		log.Fatal(err)
	}
}
