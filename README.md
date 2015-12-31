# Perf

This is an experiment in discrete queueing theory measurement.
The idea is to design a simple way of reporting counters so that
we can efficiently measure performance metrics of interest.

Take performance counting of downloads out of a web server as an example.
The uploads all happen concurrently.  We are interested in numbers
that end users would be concerned with, such as their own throughput
and latency, where they really don't care what other users are doing.

Then for the server, we need to calculate throughput as a function of load.
We can do these calculations in a completely discrete manner, which avoids
almost all of the complexity of queueing theory and statistics.  The point
is to measure systems exactly, rather than trying to make predictions with
analytic models.

The first thing to note is that when a download is happening, at the beginning
of the download we simply note to some server that a download is in progress,
to simplify keeping track of the number of concurrent sessions.  When a download
completes, we record the start time and stop time and number of events that got
counted.  To simplify things we have a mutable record that gets sent for this:

```
  [start, stop, count, population]
```

If we want to report that something started, we dont know the stop time or the count,
and this report makes the population go up by one.  So we simply report zero for stop
and count.  The fact that start is greater than stop signals that this is an incomplete
record.

Then when a job completes, we report with the exact same start time as before (we kept the timestamp),
and report the stop time and number of events.  The population goes down by one when we report
such a record.  The stop time being greater than start time signals that it is a stop record.

# Individual Job Statistics

For individual jobs, the statistic of interest is pretty easy to report.

```
   events/(stop-start)
```
This gives us a rate in events per time.  With many concurrent downloads going on, the users
do not care or know what the server needs to handle.  They only worry about their own service
level being met.  When we go to take an average measurement, note that we do not want to
do simple arithmetic means.  In the case of no concurrency, we simply want the number of observed
events divided by the observation time.  The rate reports need to be weighted such that
events with twice as much data not only have double the rate for a fixed time period, but 
will weigh twice as much.

It is a nice coincidence that the arithmetic mean weighted by time
is the same as the harmonic mean weighted by the count.  This means that we simply maintain
separate counters for events and observation time (in the non-concurrent case).

```
   (count[0] + count[1] + ... ) / ( stop[0]-start[0] + stop[1]-start[1] + ... )
```

Note:

```
  (t0*c0/t0 + t1*c1/t1 + ...)/(t0+t1+...) == 1/((c0*t0/c0 + c1*t1/c1 + ...)/(c0+c1+...))
```
The typical arithmetic mean is just where the weights are 1/n.
The harmonic mean is where we deal with inverse quantities (what you usually want for rates).

# Concurrency

If nothing happened concurrently, we would just have one pair of counters for events and observation time.
But when two events happen concurrently, we need to carefully subtract out the double-counted time.
This way, if a user has 6 concurrent sessions all experiencing 3MB/s, the counting required to
size up server throughput is kept distinct from the throughput guaranteed for a download individually.

What we really want to do with this is to calculate load dependent throughput statistics.
If we can maintain separate counters for population size (ie: queue length), then we can do a
lot of sophistocated counts:

* Utilization is just subtracting out zero population time from the total.
* Queue length distribution
* Throughput as a function of 1 user, 2 users, 4 users, ... .  This lets us measure linear scaling and bottlenecks.
* We don't need to be able to characterize a distribution analytically.
* No floating point.  It's all rational 64 bit integer arithmetic.
* Speedup - the total work divided by the total time experienced (individually) by each user, divided by
  the real time. 

Note that user interleaving behavior can cause profound performance differences.
It may be that we can have hundreds of concurrent sessions all downloading at 1MB/s,
and then there is a queue length we eventually get bottlenecked under, such that the
linear scaling stops.  When more users are downloading and we are at this point,
we also want to measure whether even total throughput begins to go down.

# De-duplicating time

The non-trivial part of this is in the algorithm to de-deduplicate time.  When time segments overlap,
we take the reports of (start,stop,count) literally and assume that there was a uniform rate for that download.
But during that time, the population size kept changing as more downloads arrived and departed.
So we use the reports of when downloads started and stopped as a mutable data structure, and patch up
the reports as departures are completed (and the arrivals padded the data structure with exactly enough
space to cut up intervals to track all changes exactly).
