# How Celery Works with Valkey: Flight Notification Demo

This document explains how Celery uses Valkey (Redis-compatible) as both a message broker and result backend, based on the flight notification system logs.

## Architecture Overview

The system uses **two separate Valkey instances**:
- **Broker** (port 6379): Handles task queuing and message passing
- **Backend** (port 6380): Stores task results and status

## Key Valkey Commands Used

### 1. Task Queuing (Broker - Port 6379)

**LPUSH** - Adds tasks to the queue
```
LPUSH "celery" "{task_data}"
```
- Tasks are pushed to the "celery" queue as JSON messages
- Each task contains serialized flight/passenger data and metadata

**BRPOP** - Workers fetch tasks from queue
```
BRPOP "celery" "celery\x06\x163" "celery\x06\x166" "celery\x06\x169" "1"
```
- Blocking pop operation - workers wait for new tasks
- Timeout of 1 second before checking again

**ZADD/ZREM** - Task acknowledgment tracking
```
ZADD "unacked_index" "timestamp" "delivery_tag"
HSET "unacked" "delivery_tag" "task_data"
```
- Tracks unacknowledged tasks to prevent loss
- Removed when task completes successfully

### 2. Result Storage (Backend - Port 6380)

**SETEX** - Store task results with expiration
```
SETEX "celery-task-meta-{task_id}" "86400" "{result_json}"
```
- Results stored for 24 hours (86400 seconds)
- Contains status, result data, and completion timestamp

**PUBLISH** - Notify result availability
```
PUBLISH "celery-task-meta-{task_id}" "{result_json}"
```
- Real-time notifications when tasks complete
- Allows immediate result retrieval

**SUBSCRIBE/GET** - Retrieve results
```
SUBSCRIBE "celery-task-meta-{task_id}"
GET "celery-task-meta-{task_id}"
```
- Subscribe for real-time updates or GET for polling

## Task Flow Example

### 1. Flight Status Update Triggered
```python
process_flight_status_update.delay(flight_data)
```

**Valkey Operations:**
- `LPUSH celery` - Main task queued
- `ZADD unacked_index` - Track for reliability

### 2. Worker Processes Main Task
- `BRPOP celery` - Worker fetches task
- `ZREM unacked_index` - Mark as acknowledged
- Creates 6 notification subtasks (email, SMS, push × 2 passengers)

### 3. Subtasks Queued
Each notification type creates separate tasks:
- `LPUSH celery` - Email tasks
- `LPUSH celery` - SMS tasks  
- `LPUSH celery` - Push notification tasks

### 4. Results Stored
As each task completes:
- `SETEX celery-task-meta-{id}` - Store result
- `PUBLISH celery-task-meta-{id}` - Notify completion

## Performance Characteristics

From the logs, we can see:
- **Email tasks**: ~1 second each
- **SMS tasks**: ~3 seconds each (slowest)
- **Push notifications**: ~0.5 seconds each
- **Task overhead**: ~20-30ms per task

## Reliability Features

1. **Unacked Message Tracking**: Tasks are tracked until completion
2. **Result Persistence**: Results stored for 24 hours
3. **Atomic Operations**: MULTI/EXEC blocks ensure consistency
4. **Heartbeat Monitoring**: Worker health tracked via PUBLISH

## Scalability Benefits

- **Parallel Processing**: Multiple workers can process different notification types simultaneously
- **Queue Persistence**: Tasks survive worker restarts
- **Result Caching**: Completed results available for retrieval
- **Load Distribution**: Work automatically distributed across available workers

This architecture allows the flight notification system to handle high volumes of status updates while maintaining reliability and providing fast response times for different notification channels.