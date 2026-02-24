# Quick Start Guide

Get the flight notification system running in under 5 minutes!

## Option 1: Docker Compose (Recommended)

The easiest way to run the entire system:

```bash
# 1. Start all services (Valkey + Workers + Flower)
docker-compose up -d

# 2. Check that all services are running
docker-compose ps

# 3. View logs
docker-compose logs -f

# 4. Run the demo (in a new terminal)
docker-compose exec worker-email python main.py

# 5. Monitor tasks at http://localhost:5555 (Flower dashboard)

# 6. Stop all services
docker-compose down
```

That's it! The system is now running with:
- ✅ Valkey message broker
- ✅ 3 Celery workers (email, sms, push)
- ✅ Flower monitoring dashboard

## Option 2: Manual Setup

### Step 1: Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Start Valkey

```bash
# Using Docker
docker run -d --name valkey -p 6379:6379 valkey/valkey:latest

# Verify it's running
docker ps
```

### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env if needed (default values work for local development)
```

### Step 4: Start Celery Workers

Open **3 terminal windows** and run one command in each:

**Terminal 1 (Email Worker):**
```bash
celery -A celery_config worker --loglevel=info -Q email -n email_worker@%h
```

**Terminal 2 (SMS Worker):**
```bash
celery -A celery_config worker --loglevel=info -Q sms -n sms_worker@%h
```

**Terminal 3 (Push Worker):**
```bash
celery -A celery_config worker --loglevel=info -Q push -n push_worker@%h
```

### Step 5: (Optional) Start Flower

In a **4th terminal:**
```bash
celery -A celery_config flower --port=5555
```

Visit http://localhost:5555 to see the monitoring dashboard.

### Step 6: Run the Demo

In a **5th terminal:**
```bash
python main.py
```

You should see:
- Flight creation with 4 passengers
- Status changes (DELAYED → BOARDING → DEPARTED)
- Notifications being sent to each passenger based on their preferences
- Task summaries showing successful deliveries

## Verification

### Check Valkey Connection
```bash
# Using redis-cli
docker exec -it valkey valkey-cli ping
# Should respond: PONG

# Or using Python
python -c "import redis; r=redis.Redis(host='localhost', port=6379); print(r.ping())"
# Should print: True
```

### Check Celery Workers
```bash
# List active workers
celery -A celery_config inspect active

# Check worker stats
celery -A celery_config inspect stats
```

### Check Task Execution
```bash
# In Flower (http://localhost:5555):
# - Navigate to "Tasks" tab
# - You should see completed tasks with status "SUCCESS"

# Or check Celery directly:
celery -A celery_config events
```

## Sample Output

When you run `python main.py`, you should see output like:

```
======================================================================
               FLIGHT NOTIFICATION SYSTEM DEMO
                    Using Celery + Valkey/Redis
======================================================================

✈️  Flight AA101 created
    Airline: American Airlines
    Route: JFK → LAX
    Passengers: 4
    Scheduled Departure: 2025-11-05 10:00 UTC
    Gate: B22

📋 Passenger Notification Preferences:
    • Alice Johnson: EMAIL, SMS, PUSH
    • Bob Smith: EMAIL, PUSH
    • Carol Williams: SMS
    • David Brown: EMAIL, SMS, PUSH

======================================================================
⏰  Simulating status change: DELAYED
======================================================================

📤 Dispatching notification tasks to Celery workers...
    Task ID: 1a2b3c4d-5e6f-7g8h-9i0j-k1l2m3n4o5p6
    Waiting for notifications to be processed...

✅ Notification Summary:
    Passengers notified: 4
    Total notifications queued: 10

    Breakdown by channel:
      EMAIL: 3 notifications
        └─ Passenger P001 (Task: 1a2b3c4d5e6f...)
        └─ Passenger P002 (Task: 2b3c4d5e6f7g...)
        └─ Passenger P004 (Task: 3c4d5e6f7g8h...)
      SMS: 3 notifications
        └─ Passenger P001 (Task: 4d5e6f7g8h9i...)
        └─ Passenger P003 (Task: 5e6f7g8h9i0j...)
        └─ Passenger P004 (Task: 6f7g8h9i0j1k...)
      PUSH: 4 notifications
        └─ Passenger P001 (Task: 7g8h9i0j1k2l...)
        └─ Passenger P002 (Task: 8h9i0j1k2l3m...)
        └─ Passenger P004 (Task: 9i0j1k2l3m4n...)

⏳ Waiting 3 seconds before next event...
```

## Troubleshooting

### "Connection refused" error
**Problem:** Can't connect to Valkey  
**Solution:** Make sure Valkey is running: `docker ps`

### "No workers available" 
**Problem:** Celery workers not running  
**Solution:** Start workers as shown in Step 4

### Tasks not executing
**Problem:** Workers started but tasks aren't processing  
**Solution:** 
1. Check worker logs for errors
2. Verify queue names match in tasks and worker commands
3. Restart workers

### Flower not accessible
**Problem:** Can't access http://localhost:5555  
**Solution:** 
1. Ensure Flower is started: `celery -A celery_config flower`
2. Check if port 5555 is available: `lsof -i :5555`

## Next Steps

1. **Read the full README.md** for detailed documentation
2. **Explore the code** in `models.py`, `tasks.py`, and `main.py`
3. **Customize notifications** by modifying message templates
4. **Add real integrations** with AWS SES, Twilio, FCM, etc.
5. **Scale workers** by running multiple instances
6. **Monitor production** with Flower and logging

## Production Deployment

For production deployment:

1. **Use managed Valkey/Redis** (AWS ElastiCache, Redis Cloud)
2. **Deploy workers** as containers (Kubernetes, ECS)
3. **Add monitoring** (CloudWatch, Datadog, Prometheus)
4. **Implement authentication** for Valkey and Flower
5. **Set up CI/CD** for automated deployments
6. **Add health checks** and auto-scaling

## Getting Help

- **Documentation:** See README.md
- **Valkey Community:** https://valkey.io
- **Celery Docs:** https://docs.celeryproject.org
- **Issues:** Open an issue on GitHub

Happy coding! 🚀
