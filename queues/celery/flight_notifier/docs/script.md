# YouTube Demo Script: Flight Notifier - Celery + Valkey

**Duration:** 4 minutes  
**Target Audience:** Python developers interested in async task processing  
**Hook:** Real-world scalable notification system demo

---

## 🎬 Opening Hook (0:00 - 0:20)

**[Screen: Terminal with project structure visible]**

> "What happens when a flight gets delayed and you need to notify thousands of passengers instantly? Today I'm showing you how to build a bulletproof notification system using Celery and Valkey that processes emails, SMS, and push notifications in parallel."

**[Quick preview: Show terminal with multiple workers processing tasks simultaneously]**

> "By the end of this video, you'll see how this system handles 6 different notification tasks concurrently with fault-tolerant queuing."

---

## 📋 Project Overview (0:20 - 0:50)

**[Screen: README.md file open]**

> "This is a flight notification system that demonstrates real-world async processing. Here's what we're building:"

**[Highlight key features in README]**
- ✅ Asynchronous task processing with Celery
- ✅ Valkey as message broker and result backend  
- ✅ Parallel notification delivery (email, SMS, push)
- ✅ Fault-tolerant task queuing

**[Screen: Show architecture diagram or code structure]**

> "The architecture is simple but powerful - we have Valkey running on two ports: 6379 for task queuing and 6380 for storing results. Workers process notifications in parallel while the main app stays responsive."

---

## 🏗️ Architecture Deep Dive (0:50 - 1:30)

**[Screen: tasks.py file open, scroll through key functions]**

> "Let's look at the code. Here's our main task that gets triggered when a flight status changes."

**[Highlight process_flight_status_update function]**

> "When a flight gets delayed, this function creates individual notification tasks for each passenger. Notice how we're using Pydantic models for type safety."

**[Scroll to individual task functions]**

> "Each notification type has different timing characteristics - emails take 1 second, SMS takes 3 seconds because of carrier delays, and push notifications are fastest at half a second."

**[Screen: models.py briefly]**

> "We're using Pydantic for clean data validation - passengers have email, phone, and optional push tokens."

---

## 🚀 Live Demo Setup (1:30 - 2:00)

**[Screen: Terminal split view]**

> "Let's see this in action. First, I'll start our Valkey instances."

```bash
# Show running Docker containers
docker ps
```

> "I already have Valkey running on ports 6379 and 6380. Now let's start a Celery worker."

**[Terminal 1]**
```bash
uv run celery -A tasks worker --loglevel=info
```

**[Show worker starting up, connecting to broker]**

> "Perfect! The worker is connected and ready to process tasks. Notice it's connected to both our broker and backend."

---

## ⚡ Live Demo Execution (2:00 - 3:20)

**[Screen: Split terminal - worker on left, trigger on right]**

> "Now for the magic. I'm going to trigger a flight delay notification."

**[Terminal 2]**
```bash
uv run python main.py
```

**[Show main.py execution]**

> "Watch what happens - the main app immediately queues the task and continues. But look at the worker terminal..."

**[Focus on worker terminal showing parallel processing]**

> "This is beautiful! Six tasks are processing simultaneously:
- Two email notifications starting
- Two SMS notifications starting  
- Two push notifications starting"

**[Point out timing differences]**

> "See how the push notifications complete first at 0.5 seconds, then emails at 1 second, and SMS takes the full 3 seconds? This is real parallel processing - we're not waiting for slow SMS to block fast push notifications."

**[Show second flight trigger]**

> "Let me trigger another flight status change to show how it scales."

**[Show boarding notification processing]**

> "Even with multiple flights, each notification type processes independently. In a real system, you'd have multiple workers handling hundreds of these concurrently."

---

## 🔍 Behind the Scenes (3:20 - 3:50)

**[Screen: Show logs directory or Valkey operations]**

> "What makes this reliable? Valkey is doing some heavy lifting behind the scenes."

**[If showing logs or Valkey CLI]**

> "Tasks are queued with LPUSH, workers fetch with BRPOP, and there's automatic tracking of unacknowledged messages. If a worker crashes, tasks don't get lost."

**[Screen: Show result storage concept]**

> "Results are stored for 24 hours, so you can check notification status later. This isn't just fire-and-forget - it's enterprise-grade reliability."

---

## 🎯 Wrap-up & Call to Action (3:50 - 4:00)

**[Screen: Back to project overview or terminal summary]**

> "And that's how you build a scalable notification system! This pattern works for any async processing - image resizing, report generation, data processing."

> "The code is in the description. Try it yourself and let me know what you build with Celery and Valkey. Subscribe for more Python architecture videos!"

**[End screen with subscribe button]**

---

## 📝 Preparation Checklist

### Before Recording:
- [ ] Valkey containers running on ports 6379 and 6380
- [ ] Terminal configured with split view
- [ ] Project dependencies installed (`uv sync`)
- [ ] Test run to ensure smooth execution
- [ ] Screen recording software ready (1080p minimum)

### Key Talking Points to Emphasize:
- **Parallel processing** - Multiple notification types running simultaneously
- **Fault tolerance** - Tasks don't get lost if workers crash  
- **Real-world timing** - Different notification channels have different speeds
- **Scalability** - Easy to add more workers for higher throughput
- **Type safety** - Pydantic models prevent runtime errors

### Visual Highlights:
- Split terminal showing worker logs and task triggers
- Timing differences between notification types
- Multiple tasks processing simultaneously
- Clean, readable code structure

### Potential Extensions (if time allows):
- Show Flower monitoring UI
- Demonstrate worker scaling
- Show task retry mechanisms
- Display Valkey CLI operations