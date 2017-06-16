# Runs a given number of the Python message producer Docker containers
# as background processes
param([int]$count, [int]$max_messages)

For ($i=1; $i -le $count; $i++)
{
    Start-Job -Name producer_$i -ScriptBlock {
        param([int]$j, [int]$messages)
        docker run --rm --name producer_$j --network container:activemq_1 proton-producer -b user:password@localhost:5672 -t some_topic -m $messages -s producer_$j
#        docker run --rm --name producer_$j --network container:activemq_1 proton-producer -b user:password@localhost:5672 -q some_queue -m $messages -s producer_$j
    } -Arg $i,$max_messages
}
