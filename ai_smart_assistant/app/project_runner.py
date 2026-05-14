import os
import subprocess
import random
import string
import shutil
import json
import time
from typing import Dict, Optional

from .workspace_fs import ensure_workspace, safe_join

PROJECTS_DIR_NAME = 'projects'

# In-memory instance registry: instance_id -> {container_id, port, project_path, started_at}
_INSTANCES: Dict[str, Dict] = {}


def _rand_id(n=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))


def projects_root() -> str:
    root = ensure_workspace()
    p = os.path.join(root, PROJECTS_DIR_NAME)
    os.makedirs(p, exist_ok=True)
    return p


def create_project(name: str, template: str) -> Optional[str]:
    rid = _rand_id(6)
    safe_name = ''.join(c if c.isalnum() or c in ('-', '_') else '-' for c in name.lower())
    folder = f"{safe_name}-{rid}"
    proj_path = os.path.join(projects_root(), folder)
    try:
        os.makedirs(proj_path, exist_ok=False)
    except Exception:
        return None

    # scaffold templates
    if template == 'static':
        index = """<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Static Site</title></head><body><h1>Welcome to your Static Project</h1><p>Edit files in the workspace/projects folder.</p></body></html>"""
        with open(os.path.join(proj_path, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(index)
    elif template == 'node':
        # simple express server
        pkg = {
            'name': safe_name,
            'version': '1.0.0',
            'main': 'index.js',
            'scripts': {'start': 'node index.js'}
        }
        server = """const express = require('express');const app = express();app.use(express.static('.'));app.get('/health', (req,res)=>res.send('ok'));const port = process.env.PORT||8080;app.listen(port, ()=>console.log('Listening',port));"""
        with open(os.path.join(proj_path, 'package.json'), 'w', encoding='utf-8') as f:
            json.dump(pkg, f, indent=2)
        with open(os.path.join(proj_path, 'index.js'), 'w', encoding='utf-8') as f:
            f.write(server)
        # add sample html
        with open(os.path.join(proj_path, 'index.html'), 'w', encoding='utf-8') as f:
            f.write('<!doctype html><html><body><h1>Node Static Project</h1><p>Edit and run.</p></body></html>')
    else:
        # default to static
        with open(os.path.join(proj_path, 'index.html'), 'w', encoding='utf-8') as f:
            f.write('<h1>Empty Project</h1>')

    return folder


def _find_free_port() -> int:
    # choose a random high port (basic approach)
    return random.randint(30000, 40000)


def run_project(project_folder: str) -> Optional[Dict]:
    proj_path = safe_join(os.path.join(PROJECTS_DIR_NAME, project_folder))
    if not proj_path or not os.path.isdir(proj_path):
        return None

    port = _find_free_port()
    instance_id = _rand_id(8)
    container_name = f'nexusproj_{instance_id}'

    # Decide runtime based on project contents
    cmd = None
    image = None
    if os.path.exists(os.path.join(proj_path, 'package.json')):
        # use node image and run npm install then start via npm start
        image = 'node:18-slim'
        # We'll mount and run: sh -c "npm install --production || true; npm start"
        cmd = [
            'docker', 'run', '-d', '--name', container_name,
            '-p', f'{port}:8080',
            '-v', f'{proj_path}:/srv',
            '-w', '/srv',
            image,
            'sh', '-c', 'npm install --production || true; NODE_ENV=production PORT=8080 npm start'
        ]
    else:
        # static: use python http.server
        image = 'python:3.11-slim'
        cmd = [
            'docker', 'run', '-d', '--name', container_name,
            '-p', f'{port}:8080',
            '-v', f'{proj_path}:/srv',
            '-w', '/srv',
            image,
            'sh', '-c', 'python -m http.server 8080'
        ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if proc.returncode != 0:
            return {'error': proc.stderr}
        container_id = proc.stdout.strip()
        _INSTANCES[instance_id] = {
            'container_id': container_id,
            'port': port,
            'project': project_folder,
            'started_at': time.time(),
            'container_name': container_name
        }
        return {'instance_id': instance_id, 'port': port}
    except Exception as e:
        return {'error': str(e)}


def stop_instance(instance_id: str) -> Dict:
    info = _INSTANCES.get(instance_id)
    if not info:
        return {'error': 'instance not found'}
    container_name = info.get('container_name')
    try:
        subprocess.run(['docker', 'stop', container_name], capture_output=True, timeout=20)
        subprocess.run(['docker', 'rm', '-f', container_name], capture_output=True, timeout=20)
    except Exception as e:
        return {'error': str(e)}
    _INSTANCES.pop(instance_id, None)
    return {'stopped': True}


def list_instances() -> Dict:
    return _INSTANCES.copy()
