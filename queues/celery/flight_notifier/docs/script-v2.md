# YouTube Demo Script v2: Flight Notifier - Terminal-Only Demo

**Duration:** 4 minutes  
**Target Audience:** Python developers interested in async task processing  
**Style:** Terminal-focused with `bat`/`glow` for code display

---

## 🎬 Opening Hook (0:00 - 0:20)

**[Terminal: Clear screen, show project tree with `tree` or `ls -la`]**

> "What happens when a flight gets delayed and you need to notify thousands of passengers instantly? Today I'm showcasing a reliable notification system using Celery and Valkey."

**[Quick preview: `ps aux | grep celery` showing worker processes]**

> "By the end of this video, you'll see parallel task processing in action with real-time logs showing 6 different notification tasks running simultaneously."

---

## 📋 Project Overview (0:20 - 0:50)

**[Terminal: `glow README.md` or `bat README.md`]**

> "Here's what we're building - a flight notification system that demonstrates real-world async processing."

**[Scroll through README highlighting key features]**

> "The architecture is beautifully simple - Valkey handles task queuing on port 6379 and result storage on 6380. Workers process notifications in parallel while the main app stays completely responsive."

**[Terminal: `bat pyproject.toml`]**

> "Just a few dependencies - Celery for task processing, Pydantic for type safety, and Valkey as our broker and backend."

---

## 🏗️ Code Walkthrough (0:50 - 1:30)

**[Terminal: `bat models.py`]**

> "Let's look at our data models. Clean Pydantic classes for type safety - passengers have email, phone, and optional push tokens."

**[Terminal: `bat tasks.py` - scroll to show task functions]**

> "Here's where the magic happens. Each notification type has realistic timing - emails take 1 second, SMS takes 3 seconds due to carrier delays, and push notifications are fastest at half a second."

**[Highlight the main task function]**

> "When a flight status changes, this main task fans out individual notifications for each passenger. Notice how we serialize Pydantic models as dictionaries for Celery."

**[Terminal: `bat main.py`]**

> "And here's our trigger - simulating flight delays and boarding announcements. The main app queues tasks and immediately continues."

---

## 🚀 Infrastructure Setup (1:30 - 1:50)

**[Terminal: `docker ps`]**

> "First, let's check our Valkey instances are running."

**[Show containers running on ports 6379 and 6380]**

> "Perfect - broker on 6379, backend on 6380. Now let's start our worker."

**[Terminal: Split screen setup with `tmux` or multiple terminal windows]**

> "I'm using tmux to split my terminal - worker logs on the left, commands on the right."

---

## ⚡ Live Demo - Worker Startup (1:50 - 2:10)

**[Left pane: Start Celery worker]**
```bash
uv run celery -A tasks worker --loglevel=info
```

**[Show worker connecting and registering tasks]**

> "Beautiful! The worker is connected to both broker and backend. Look at those registered tasks - our three notification types plus the main orchestrator."

**[Right pane: Show worker status]**
```bash
uv run celery -A tasks inspect active
```

> "Worker is ready and waiting for tasks. Now for the real magic."

---

## 🔥 Live Demo - Parallel Processing (2:10 - 3:20)

**[Right pane: Trigger first flight update]**
```bash
uv run python main.py
```

**[Focus on left pane - worker logs]**

> "Watch this! The main task immediately fans out to 6 individual tasks. Look at the timestamps - they're all starting simultaneously!"

**[Point out parallel execution in logs]**

> "This is real parallel processing:
- Email tasks starting for both passengers
- SMS tasks starting in parallel  
- Push notifications firing off
- All happening at the same time!"

**[Show completion timing]**

> "See the completion pattern? Push notifications finish first at 1.5 seconds, emails at 2 seconds, and SMS takes the full 3 seconds. We're not blocking fast notifications waiting for slow ones."

**[Right pane: Check task status]**
```bash
uv run celery -A tasks inspect stats
```

> "Look at those stats - processed tasks, active workers, all tracked in real-time."

---

## 📊 Monitoring & Reliability (3:20 - 3:45)

**[Right pane: Show Valkey operations]**
```bash
valkey-cli -p 6379 MONITOR
```

**[In another pane, trigger another flight update]**

> "Let me show you what's happening under the hood. This is Valkey monitoring every operation - LPUSH for queuing tasks, BRPOP for workers fetching them."

**[Stop monitor, show result storage]**
```bash
valkey-cli -p 6380 SCAN 0 MATCH "celery-task-meta-*" COUNT 10
```

> "And here are our task results, stored for 24 hours. This isn't fire-and-forget - it's enterprise-grade reliability with full audit trails."

**[Show worker scaling potential]**
```bash
# In background: uv run celery -A tasks worker --loglevel=info --concurrency=4
```

> "Want more throughput? Just add more workers. Celery automatically distributes the load."

---

## 🎯 Wrap-up (3:45 - 4:00)

**[Terminal: Clear screen, show project structure again]**

> "And that's how you build production-ready async processing! This pattern scales from dozens to millions of tasks."

**[Show final stats or summary]**

> "The complete code is in the description. Try it yourself - build notification systems, image processing, data pipelines - anything that needs reliable async work."

> "Subscribe for more terminal-driven Python architecture! Next week: building this same system with FastAPI webhooks."

---

## 📝 Terminal Setup Checklist

### Pre-recording Setup:
- [ ] **tmux session** configured with 3 panes:
  - Left: Celery worker logs
  - Right-top: Command execution  
  - Right-bottom: Monitoring/stats
- [ ] **Valkey containers** running and verified
- [ ] **Terminal theme** optimized for recording (high contrast)
- [ ] **Font size** increased for video clarity
- [ ] **bat/glow** configured with syntax highlighting theme

### Key Commands Ready:
```bash
# Core demo commands
uv run celery -A tasks worker --loglevel=info
uv run python main.py
uv run celery -A tasks inspect active
uv run celery -A tasks inspect stats

# Code display commands  
bat models.py
bat tasks.py
bat main.py
glow README.md

# Monitoring commands
docker ps
redis-cli -p 6379 monitor
redis-cli -p 6380 keys "celery-task-meta-*"
```

### Terminal Aesthetics:
- **Color scheme**: Dark background with bright syntax highlighting
- **Font**: Monospace font optimized for screen recording
- **Window size**: Full screen or large enough for clear text
- **Prompt**: Clean, minimal PS1 prompt

### Timing Cues:
- **0:20** - Switch to `glow README.md`
- **0:50** - Start `bat` code walkthrough
- **1:30** - Switch to `docker ps`
- **1:50** - Split terminal with tmux
- **2:10** - Start main demo execution
- **3:20** - Begin monitoring section

### Pro Tips:
- **Clear terminal** between major sections for clean transitions
- **Use aliases** for long commands to avoid typing errors
- **Pre-position** in correct directories to avoid `cd` commands
- **Test run** the entire sequence to ensure smooth flow
- **Have backup** commands ready if something fails

This terminal-focused approach will create a more authentic developer experience and showcase the real-time nature of async processing beautifully!