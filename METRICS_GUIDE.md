# Prometheus Metrics Guide

## What Are Metrics?

**Metrics** are numerical measurements that tell you how your application is performing. Think of them like a car's dashboard:
- **Speedometer** = Request rate (requests/second)
- **Fuel gauge** = Memory usage
- **Temperature** = CPU usage
- **Odometer** = Total requests served

Instead of saying "the API feels slow," metrics let you say "95% of requests take less than 500ms."

---

## Viewing Metrics

### API Gateway Metrics
```bash
curl http://localhost:8000/metrics
```

### Ingestion Service Metrics
```bash
curl http://localhost:8001/metrics
```

Or open in browser:
- API Gateway: http://localhost:8000/metrics
- Ingestion Service: http://localhost:8001/metrics

**Note:** The `/metrics` endpoint is public (no API key required) so monitoring tools like Prometheus can scrape it.

---

## What Metrics Are Available Right Now

Your services currently expose **system-level metrics** (Python runtime and process stats). These are valuable for monitoring application health:

### **Python Runtime Metrics**

#### `python_gc_objects_collected_total`
**What it is:** Number of objects cleaned up by Python's garbage collector

**Example:**
```prometheus
python_gc_objects_collected_total{generation="0"} 2435.0
python_gc_objects_collected_total{generation="1"} 11792.0
```

**Why it matters:** High numbers might indicate memory churn (creating/destroying lots of objects)

---

#### `python_gc_collections_total`
**What it is:** How many times garbage collection has run

**Example:**
```prometheus
python_gc_collections_total{generation="0"} 169.0
```

**Why it matters:** Frequent GC can slow down your application

---

#### `python_info`
**What it is:** Python version information

**Example:**
```prometheus
python_info{implementation="CPython",major="3",minor="11",version="3.11.14"} 1.0
```

**Why it matters:** Helps verify you're running the correct Python version

---

### **Process Metrics**

#### `process_virtual_memory_bytes`
**What it is:** Total virtual memory allocated (includes memory on disk)

**Example:**
```prometheus
process_virtual_memory_bytes 172261376  # ~172 MB
```

**Why it matters:**
- Growing over time = possible memory leak
- Too high = might run out of memory

**When to worry:** If it keeps growing and never goes down

---

#### `process_resident_memory_bytes`
**What it is:** Actual RAM being used (physical memory)

**Example:**
```prometheus
process_resident_memory_bytes 59166720  # ~59 MB
```

**Why it matters:** This is your "real" memory usage
- If this hits your container limit → service crashes
- Normal range for small FastAPI app: 50-200 MB

**When to worry:** If it exceeds 500 MB or grows continuously

---

#### `process_cpu_seconds_total`
**What it is:** Total CPU time consumed since service started

**Example:**
```prometheus
process_cpu_seconds_total 1.09  # 1.09 seconds of CPU time
```

**Why it matters:**
- Divide by uptime to get average CPU usage
- Rapidly growing = CPU-intensive operations

**Calculation:**
```
CPU usage % = (cpu_seconds_total / uptime_seconds) * 100
```

---

#### `process_open_fds`
**What it is:** Number of open file descriptors (files, sockets, connections)

**Example:**
```prometheus
process_open_fds 17.0
process_max_fds 1048576.0
```

**Why it matters:**
- Each HTTP connection, file, database connection uses a file descriptor
- If `open_fds` approaches `max_fds` → you're leaking connections

**When to worry:** If it keeps growing and reaches max_fds (will cause "too many open files" errors)

---

#### `process_start_time_seconds`
**What it is:** When the service started (Unix timestamp)

**Example:**
```prometheus
process_start_time_seconds 1762797808.05
```

**Why it matters:** Calculate uptime
```
uptime = current_time - start_time
```

**Use case:** Detect unexpected restarts/crashes

---

## HTTP Request Metrics (Future/Advanced)

**Note:** The following HTTP metrics are configured but may not appear until requests are made or Prometheus Instrumentator is fully integrated.

### 1. **Request Count** (`http_requests_total`)
**What it is:** Total number of HTTP requests to each endpoint

**Example:**
```prometheus
http_requests_total{method="GET",handler="/health",status="200"} 45
http_requests_total{method="POST",handler="/upload",status="200"} 12
http_requests_total{method="POST",handler="/upload",status="400"} 3
```

**Why it matters:**
- See which endpoints are most popular
- Track error rates (non-200 status codes)
- Monitor API usage trends

**Calculation:**
```
Error rate = (requests with status 500) / (total requests) * 100%
```

---

### 2. **Request Duration** (`http_request_duration_seconds`)
Tracks how long each request takes.

```prometheus
http_request_duration_seconds_sum{method="POST",handler="/upload"} 24.5
http_request_duration_seconds_count{method="POST",handler="/upload"} 10
```

**Calculation:**
- Average duration = sum / count = 24.5 / 10 = 2.45 seconds per request

**Use cases:**
- Identify slow endpoints
- Detect performance regressions
- Set SLA targets (e.g., 95% of requests < 1s)

---

### 3. **Requests In Progress** (`http_requests_inprogress`)
Tracks active requests currently being processed.

```prometheus
http_requests_inprogress{method="POST",handler="/upload"} 3
```

**Use cases:**
- Monitor server load
- Detect if requests are piling up (overload)
- Capacity planning

---

### 4. **HTTP Status Codes**
Broken down by status code:

```prometheus
http_requests_total{status="200"} 100  # Success
http_requests_total{status="400"} 5    # Bad request
http_requests_total{status="401"} 10   # Unauthorized
http_requests_total{status="500"} 2    # Server error
```

**Use cases:**
- Track error rates
- Monitor authentication failures (401/403)
- Alert on server errors (500+)

---

## Example Metrics Output

```prometheus
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{handler="/health",method="GET",status="200"} 45.0

# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{handler="/upload",le="0.1",method="POST"} 3.0
http_request_duration_seconds_bucket{handler="/upload",le="0.5",method="POST"} 7.0
http_request_duration_seconds_bucket{handler="/upload",le="1.0",method="POST"} 10.0
http_request_duration_seconds_sum{handler="/upload",method="POST"} 12.5
http_request_duration_seconds_count{handler="/upload",method="POST"} 10.0

# HELP http_requests_inprogress Number of HTTP requests in progress
# TYPE http_requests_inprogress gauge
http_requests_inprogress{handler="/upload",method="POST"} 2.0
```

---

## Common Queries

### 1. **Average Response Time**
```
http_request_duration_seconds_sum / http_request_duration_seconds_count
```

### 2. **Request Rate (requests per second)**
```
rate(http_requests_total[5m])
```

### 3. **Error Rate**
```
rate(http_requests_total{status=~"5.."}[5m])
```

### 4. **95th Percentile Response Time**
```
histogram_quantile(0.95, http_request_duration_seconds_bucket)
```

---

## What to Monitor

### 🚨 **Alerts to Set Up**

1. **High Error Rate**
   - If error rate > 5% → Alert
   - Something is broken

2. **Slow Responses**
   - If 95th percentile > 5 seconds → Alert
   - Performance degradation

3. **Too Many In-Progress Requests**
   - If inprogress > 100 → Alert
   - Server is overloaded

4. **Authentication Failures**
   - If 401/403 spikes → Alert
   - Possible attack or misconfiguration

---

## Setting Up Prometheus (Optional)

### 1. **Create prometheus.yml**
```yaml
scrape_configs:
  - job_name: 'api-gateway'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'

  - job_name: 'ingestion-service'
    static_configs:
      - targets: ['localhost:8001']
    metrics_path: '/metrics'
```

### 2. **Run Prometheus in Docker**
```bash
docker run -d \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

### 3. **View in Prometheus UI**
```
http://localhost:9090
```

---

## Setting Up Grafana (Optional)

### 1. **Run Grafana**
```bash
docker run -d -p 3000:3000 grafana/grafana
```

### 2. **Add Prometheus Data Source**
- URL: `http://prometheus:9090`

### 3. **Import Dashboard**
Use pre-built FastAPI dashboard:
- Dashboard ID: `14410` (FastAPI Observability)

---

## Metrics in Production

When deployed to production:

1. **Use Prometheus Server**
   - Scrapes metrics every 15-30 seconds
   - Stores historical data

2. **Use Grafana for Visualization**
   - Beautiful dashboards
   - Alerting rules
   - Email/Slack notifications

3. **Use AlertManager**
   - Send alerts to PagerDuty, Slack, Email
   - On-call rotation

---

## Quick Health Check

```bash
# Make some requests to generate metrics
curl http://localhost:8000/health
curl -H "X-API-Key: dev-key-change-in-production" http://localhost:8000/info

# View metrics
curl http://localhost:8000/metrics | grep http_requests_total
```

Expected output:
```
http_requests_total{handler="/health",method="GET",status="200"} 1.0
http_requests_total{handler="/info",method="GET",status="200"} 1.0
```

---

## Why Metrics Matter

### Before Metrics:
- "The API feels slow" (no proof)
- "We had some errors yesterday" (how many?)
- "Traffic is increasing" (by how much?)

### With Metrics:
- "95th percentile response time increased from 500ms to 2s"
- "Error rate is 15% (30 out of 200 requests)"
- "Traffic grew 300% (1000 → 4000 requests/hour)"

**Metrics give you data-driven insights!**

---

## Practical Example: Reading Your Metrics

Let's say you open `http://localhost:8000/metrics` and see:

```prometheus
process_resident_memory_bytes 62914560
process_cpu_seconds_total 2.5
process_start_time_seconds 1731268800
process_open_fds 19
```

**What does this tell you?**

### Memory Usage
```
62914560 bytes = 62.9 MB = 0.062 GB
```
✅ **Status:** Healthy - normal for a FastAPI service

### CPU Usage
Service has used **2.5 seconds** of CPU time since it started.

If it started 100 seconds ago:
```
CPU usage = (2.5 / 100) * 100 = 2.5%
```
✅ **Status:** Low CPU usage - service is idle or efficient

### Open Connections
```
19 file descriptors open (out of 1,048,576 max)
```
✅ **Status:** Plenty of headroom

### Uptime
```
current_time = 1731268900 (example)
start_time = 1731268800
uptime = 100 seconds = 1 minute 40 seconds
```

---

## Real-World Monitoring Scenarios

### Scenario 1: Memory Leak Detection
**Day 1:** `process_resident_memory_bytes 60000000` (60 MB)
**Day 2:** `process_resident_memory_bytes 120000000` (120 MB)
**Day 3:** `process_resident_memory_bytes 240000000` (240 MB)

🚨 **Problem:** Memory is doubling every day → **memory leak!**

**Action:** Investigate what's keeping objects in memory

---

### Scenario 2: File Descriptor Leak
**Hour 1:** `process_open_fds 20`
**Hour 2:** `process_open_fds 150`
**Hour 3:** `process_open_fds 450`

🚨 **Problem:** File descriptors growing → **connection leak!**

**Action:** Check if HTTP connections or database connections aren't being closed

---

### Scenario 3: Service Crash Detection
**Monday 9:00 AM:** `process_start_time_seconds 1731225600`
**Monday 11:00 AM:** `process_start_time_seconds 1731234000`

🚨 **Problem:** Start time changed → **service restarted/crashed!**

**Action:** Check logs for errors that caused the crash

---

### Scenario 4: High CPU Usage
**Normal:** `process_cpu_seconds_total` grows by 0.5 every minute
**Spike:** `process_cpu_seconds_total` grows by 5.0 every minute

🚨 **Problem:** 10x CPU increase → something is processing heavily

**Action:** Check if a PDF processing job is stuck or a loop is running

---

## How Prometheus Would Use These Metrics

If you set up Prometheus (optional, for later), it would:

1. **Scrape metrics every 15 seconds:**
   ```
   GET http://localhost:8000/metrics  (every 15s)
   GET http://localhost:8001/metrics  (every 15s)
   ```

2. **Store historical data** so you can see trends over days/weeks

3. **Create queries** like:
   ```promql
   # Show memory growth over last 24 hours
   rate(process_resident_memory_bytes[24h])

   # Alert if memory > 500 MB
   process_resident_memory_bytes > 500000000
   ```

4. **Send alerts** via email/Slack when thresholds are crossed

---

## Summary: What You Have Now

✅ **Working metrics endpoint:** `/metrics` on both services
✅ **System metrics:** Memory, CPU, file descriptors, Python GC
✅ **Production-ready:** These metrics are used in real production systems
✅ **No auth required:** Prometheus can scrape them easily

🔜 **Future (Week 2+):** HTTP request metrics will show as traffic increases
🔜 **Optional:** Set up Prometheus + Grafana for beautiful dashboards

---

## Next Steps

1. ✅ Metrics are now exposed at `/metrics`
2. ✅ You understand what each metric means
3. ⏭️ (Later) Set up Prometheus to scrape metrics
4. ⏭️ (Later) Set up Grafana for visualization
5. ⏭️ (Later) Configure alerts for production

**For now:** You can view raw metrics at `/metrics` endpoint and monitor system health!
