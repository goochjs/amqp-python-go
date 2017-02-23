package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"sync"

	"qpid.apache.org/amqp"
	"qpid.apache.org/electron"
)

// Usage and command-line flags
func usage() {
	fmt.Fprintf(os.Stderr, `Usage: %s url [url ...]
Send messages to each URL concurrently with body "<url-path>-<n>" where n is the message number.
`, os.Args[0])
	flag.PrintDefaults()
}

var count = flag.Int64("count", 1, "Send this may messages per address.")
var messageDest = flag.String("dest", "topic://some_topic", "[topic|queue]://{name}")
var debug = flag.Bool("debug", false, "Print detailed debug output")
var debugf = func(format string, data ...interface{}) {} // Default no debugging output

func main() {
	flag.Usage = usage
	flag.Parse()

	if *debug {
		debugf = func(format string, data ...interface{}) { log.Printf(format, data...) }
	}

	urls := flag.Args() // Non-flag arguments are URLs to receive from
	if len(urls) == 0 {
		log.Println("No URL provided")
		flag.Usage()
		os.Exit(1)
	}

	sentChan := make(chan electron.Outcome) // Channel to receive acknowledgements.

	var wait sync.WaitGroup
	wait.Add(len(urls)) // Wait for one goroutine per URL.

	container := electron.NewContainer(fmt.Sprintf("send[%v]", os.Getpid()))
	connections := make(chan electron.Connection, len(urls)) // Connctions to close on exit

	// Start a goroutine for each URL to send messages.
	for _, urlStr := range urls {
		debugf("Connecting to %v\n", urlStr)
		go func(urlStr string) {
			defer wait.Done() // Notify main() when this goroutine is done.
			url, err := amqp.ParseURL(urlStr)
			fatalIf(err)
			c, err := container.Dial("tcp", url.Host)
			fatalIf(err)
			connections <- c // Save connection so we can Close() when main() ends
			debugf("Message destination %s\n", *messageDest)
			s, err := c.Sender(electron.Target(*messageDest))
			fatalIf(err)
			// Loop sending messages.
			for i := int64(0); i < *count; i++ {
				m := amqp.NewMessage()
				body := fmt.Sprintf("%v%v", url.Path, i)
				m.Marshal(body)
				s.SendAsync(m, sentChan, body) // Outcome will be sent to sentChan
			}
		}(urlStr)
	}

	// Wait for all the acknowledgements
	expect := int(*count) * len(urls)
	debugf("Started senders, expect %v acknowledgements\n", expect)
	for i := 0; i < expect; i++ {
		out := <-sentChan // Outcome of async sends.
		if out.Error != nil {
			log.Fatalf("acknowledgement[%v] %v error: %v", i, out.Value, out.Error)
		} else if out.Status != electron.Accepted {
			log.Fatalf("acknowledgement[%v] unexpected status: %v", i, out.Status)
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

func fatalIf(err error) {
	if err != nil {
		log.Fatal(err)
	}
}
