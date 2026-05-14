# Project Runner (MVP)

This feature allows creating, running, and previewing simple projects inside Docker containers.

Features

- Create project from templates (Static HTML, Node).
- Run project in a sandboxed Docker container with a random high host port.
- Preview the running app in an iframe.
- Stop the running instance.

Endpoints

- `POST /projects/create` - JSON { name, template } -> { success, project_id }
- `POST /projects/run` - JSON { project_id } -> { success, instance_id, port, url }
- `POST /projects/stop` - JSON { instance_id } -> { success }
- `GET /projects/list` - lists available projects and running instances

Usage

1. Ensure Docker is installed and the current user can run `docker` commands.
2. Start the Flask app.
3. Open NexusAI in the browser, click **New Project** → choose template → **Create & Run**.

Security

This MVP runs user projects in Docker containers with mounted project folders. For production you should:

- Run containers under a restricted user or script that enforces resource and network policies.
- Use a dedicated container runtime or orchestrator to isolate workloads.
- Sanitize user inputs and limit allowed templates and commands.

Limitations

- This MVP uses the Docker CLI and in-memory instance tracking; it is not resilient across server restarts.
- For scaling, replace with a job queue and worker pool (Redis + RQ or Celery) and persistent metadata storage.

