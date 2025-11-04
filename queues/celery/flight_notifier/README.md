# Flight Notifier - Celery + Valkey Demo

A demonstration of using Celery with Valkey (Redis-compatible) for asynchronous task processing in a flight notification system.

## Overview

This project shows how to build a scalable notification system that processes flight status updates and sends notifications (email, SMS, push) to passengers asynchronously using Celery and Valkey.

**Key Features:**
- Asynchronous task processing with Celery
- Valkey as message broker and result backend
- Parallel notification delivery (email, SMS, push)
- Fault-tolerant task queuing
- Real-time task monitoring

## Architecture

- **Broker** (Valkey port 6379): Task queuing and message passing
- **Backend** (Valkey port 6380): Task results and status storage
- **Workers**: Process notification tasks in parallel
- **Producer**: Flight API that triggers status updates

## Quick Start

### Prerequisites
- Python 3.8+
- Valkey/Redis server
- uv (Python package manager)

### 1. Setup
```bash
# Install dependencies
uv sync

# Start Valkey instances
docker run -d -p 6379:6379 --name valkey-broker valkey/valkey:latest
docker run -d -p 6380:6380 --name valkey-backend valkey/valkey:latest
```

### 2. Start Celery Worker
```bash
uv run celery -A tasks worker --loglevel=info
```

### 3. Trigger Flight Updates
```bash
uv run python main.py
```

### 4. Monitor Results
Watch the worker terminal to see parallel processing of:
- Email notifications (~1s each)
- SMS notifications (~3s each) 
- Push notifications (~0.5s each)

## Project Structure

```
flight_notifier/
├── main.py          # Flight status trigger (producer)
├── tasks.py         # Celery tasks and configuration
├── models.py        # Pydantic data models
├── docs/
│   └── demo.md      # Detailed Celery-Valkey integration guide
└── logs/            # System operation logs
```

## How It Works

1. **Flight Status Change**: `main.py` detects a status change and queues a main task
2. **Task Fanout**: Main task creates individual notification tasks for each passenger
3. **Parallel Processing**: Workers process email, SMS, and push notifications simultaneously
4. **Result Storage**: Task results stored in Valkey backend for monitoring

See [docs/demo.md](docs/demo.md) for detailed technical explanation of Celery-Valkey integration.

## Performance

From actual logs:
- **Task Overhead**: ~20-30ms per task
- **Concurrent Processing**: 6 notification tasks per flight update
- **Reliability**: Unacked message tracking prevents task loss
- **Scalability**: Horizontal worker scaling supported
