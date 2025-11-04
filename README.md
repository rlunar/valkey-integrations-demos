# Valkey Integrations

A collection of practical examples and reference implementations demonstrating how to integrate [Valkey](https://valkey.io/) with popular frameworks, libraries, and tools.

## About Valkey

Valkey is a high-performance, open-source key-value datastore and the natural evolution of the Redis community. As a Linux Foundation project, Valkey provides the reliability and performance you need for production workloads, backed by a truly open governance model that ensures the project remains community-driven.

## Purpose

This repository serves as a learning resource and reference implementation for developers looking to integrate Valkey into their applications. Each integration example demonstrates real-world patterns, best practices, and production-ready configurations.

## Current Integrations

### Task Queues

#### [Celery Image Processor](./queues/celery/image-processor/)

A production-ready asynchronous image processing service that demonstrates distributed task processing with Valkey as the message broker.

**Use Case:** Automated thumbnail generation for photo-sharing applications

**Key Features:**
- Asynchronous image upload and processing
- Parallel thumbnail generation in multiple sizes (small, medium, large)
- RESTful API with Flask
- Task status tracking and result retrieval
- Scheduled cleanup tasks
- Health monitoring endpoints

**Technologies:**
- Python 3.12+
- Celery 5.5+
- Flask 3.1+
- Pillow (PIL) for image processing
- Valkey as message broker and result backend

**Learn More:** See the [detailed documentation](./queues/celery/image-processor/docs/blog.md) for architecture rationale, implementation guide, and production best practices.

## Planned Integrations

We're actively expanding this repository with more integration examples. Future additions may include:

### Task Queues
- BullMQ (Node.js)
- Sidekiq (Ruby)
- RQ (Python)
- Faktory

### Caching
- Spring Cache (Java)
- Rails Cache (Ruby)
- Django Cache (Python)
- Express Cache (Node.js)

### Session Management
- Express Session (Node.js)
- Flask-Session (Python)
- Spring Session (Java)

### Real-time Applications
- Socket.IO adapter
- Django Channels
- Rails Action Cable

### Rate Limiting
- Express Rate Limit
- Django Ratelimit
- Spring Cloud Gateway

### Message Streaming
- Valkey Streams with consumers
- Event sourcing patterns
- CQRS implementations

## Contributing

We welcome contributions! If you have an integration example you'd like to share:

1. Fork this repository
2. Create a new directory following the pattern: `category/framework/example-name/`
3. Include a comprehensive README with:
   - Clear use case description
   - Setup instructions
   - Configuration examples
   - Best practices
4. Add working code with comments
5. Submit a pull request

## Getting Started

Each integration example includes its own README with specific setup instructions. Generally, you'll need:

1. **Valkey installed and running** - See [Valkey Quick Start](https://valkey.io/docs/topics/quickstart/)
2. **Language runtime** - Python, Node.js, Java, etc., depending on the example
3. **Dependencies** - Install using the package manager for your chosen integration

## Project Structure

```
valkey-integrations/
├── queues/           # Task queue integrations
│   └── celery/       # Celery-specific examples
├── caching/          # (Coming soon) Cache integrations
├── sessions/         # (Coming soon) Session management
├── realtime/         # (Coming soon) Real-time applications
└── streaming/        # (Coming soon) Message streaming
```

## Community and Support

- **Valkey Website:** [valkey.io](https://valkey.io/)
- **Valkey Documentation:** [valkey.io/docs](https://valkey.io/docs/)
- **Valkey GitHub:** [github.com/valkey-io/valkey](https://github.com/valkey-io/valkey)
- **Community:** Join the Valkey community channels to ask questions and share experiences

## License

This project is licensed under the BSD 3-Clause License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

Special thanks to the Valkey community and all contributors who help maintain and expand these integration examples.