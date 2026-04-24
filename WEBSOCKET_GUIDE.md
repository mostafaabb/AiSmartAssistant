# WebSocket Integration Guide

## Overview

NexusAI now supports **real-time collaboration** through WebSockets, enabling:
- ✅ Live code editing (multiple users editing same file)
- ✅ Presence tracking (see who's online)
- ✅ Live cursor positions (see where others are editing)
- ✅ Chat messages (communicate during coding)
- ✅ Execution streaming (see code output in real-time)

## Backend Setup (Already Done ✅)

The backend WebSocket infrastructure is complete:

**Files Created:**
- `backend/app/services/websocket_manager.py` - Connection management
- `backend/app/api/v2/websocket.py` - WebSocket endpoint
- `ai_smart_assistant/app/assets/js/websocket-client.js` - JavaScript client

**Endpoints:**
- `ws://localhost:8000/ws/project/{project_id}/{user_id}` - Main WebSocket
- `GET /api/v2/ws/project/{project_id}/users` - Get connected users
- `GET /api/v2/ws/project/{project_id}/presence` - Get presence info

## Frontend Integration

### 1. Import WebSocket Client

```javascript
import NexusAIWebSocket from './websocket-client.js';
```

### 2. Initialize Connection

```javascript
const wsClient = new NexusAIWebSocket({
  projectId: 'project-uuid-here',
  userId: 'user-uuid-here',
  token: 'jwt-access-token',
  baseUrl: 'ws://localhost:8000',  // Optional
  
  // Callbacks for events
  onConnect: () => {
    console.log('Connected to project!');
  },
  
  onDisconnect: () => {
    console.log('Disconnected from project');
  },
  
  onCodeChange: (message) => {
    // Handle code change from another user
    const { file_id, content, user_id } = message;
    updateEditorContent(content);
  },
  
  onCursorMove: (message) => {
    // Show cursor position from another user
    const { user_id, cursor } = message;
    showRemoteCursor(user_id, cursor);
  },
  
  onChatMessage: (message) => {
    // Display chat message
    const { user_name, content } = message;
    appendChatMessage(user_name, content);
  },
  
  onPresence: (message) => {
    // Update list of online users
    const { users, count } = message;
    updateUserList(users);
  },
  
  onExecutionOutput: (message) => {
    // Stream code execution output
    const { output, error, status } = message;
    displayOutput(output, error, status);
  },
  
  onError: (error) => {
    console.error('WebSocket error:', error);
  }
});

// Connect
wsClient.connect();
```

### 3. Send Messages

```javascript
// Send code change (when user edits)
wsClient.sendCodeChange('file-id', newCodeContent);

// Send cursor position (on every cursor move)
wsClient.sendCursorMove(line, column);

// Send chat message
wsClient.sendChatMessage('Hello team!');

// Send execution result (from code runner)
wsClient.sendExecutionResult(
  executionId,
  'output text here',
  null,  // error (null if no error)
  'success'  // status: running, success, error, timeout
);
```

### 4. Disconnect

```javascript
wsClient.disconnect();
```

## Message Format

### Code Change
```javascript
{
  "type": "code_change",
  "file_id": "file-uuid",
  "content": "full file content",
  "delta": {/* optional delta for optimization */}
}
```

### Cursor Move
```javascript
{
  "type": "cursor_move",
  "line": 10,
  "column": 5
}
```

### Chat Message
```javascript
{
  "type": "chat_message",
  "content": "Hello team!"
}
```

### Execution Result
```javascript
{
  "type": "execution_result",
  "execution_id": "exec-uuid",
  "output": "Program output here",
  "error": null,  // or error message
  "status": "success"  // or "running", "error", "timeout"
}
```

### Incoming Messages

#### Presence Update
```json
{
  "type": "presence",
  "users": [
    {
      "user_id": "user-uuid",
      "user_name": "Alice",
      "cursor": {"line": 10, "column": 5},
      "connected_since": "2024-04-23T12:00:00"
    }
  ],
  "count": 2
}
```

#### Code Change (from other user)
```json
{
  "type": "code_change",
  "file_id": "file-uuid",
  "content": "updated code",
  "user_id": "other-user-uuid"
}
```

#### Chat Message
```json
{
  "type": "chat_message",
  "user_id": "user-uuid",
  "user_name": "Alice",
  "content": "Great idea!",
  "timestamp": "2024-04-23T12:00:00"
}
```

## Example: Real-Time Code Editor Integration

```javascript
// Initialize WebSocket
const ws = new NexusAIWebSocket({
  projectId: currentProject,
  userId: currentUserId,
  token: jwtToken,
  
  onConnect: () => {
    showNotification('Connected to project');
  },
  
  onCodeChange: (message) => {
    // Update editor when another user edits
    editor.setValue(message.content);
  },
  
  onCursorMove: (message) => {
    // Show remote cursor
    const color = getUserColor(message.user_id);
    showRemoteCursor(message.user_id, message.cursor, color);
  },
  
  onPresence: (message) => {
    // Update user list
    updateCollaborators(message.users);
  }
});

ws.connect();

// Send code changes
editor.on('change', (newCode) => {
  ws.sendCodeChange(currentFileId, newCode);
});

// Send cursor position
editor.on('cursorMove', (line, column) => {
  ws.sendCursorMove(line, column);
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  ws.disconnect();
});
```

## Example: Code Execution with Real-Time Output

```javascript
// Run code and stream output via WebSocket
async function executeCode() {
  const response = await fetch('/api/v2/projects/{id}/code/execute', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      code: editor.getValue(),
      language: 'python'
    })
  });
  
  const result = await response.json();
  
  // Stream result to all connected users via WebSocket
  ws.sendExecutionResult(
    result.id,
    result.output,
    result.error,
    result.status
  );
}

// Listen for execution results from other users
ws.onExecutionOutput = (message) => {
  displayOutput(message.output, message.error, message.status);
};
```

## Connection Management

### Automatic Reconnection

The WebSocket client automatically reconnects with exponential backoff:
- Attempt 1: 3 seconds
- Attempt 2: 6 seconds
- Attempt 3: 12 seconds
- Attempt 4: 24 seconds
- Attempt 5: 48 seconds

### Heartbeat

The client sends a ping every 30 seconds to keep the connection alive.

### Connection Status

```javascript
const status = ws.getStatus();
console.log({
  connected: status.connected,
  projectId: status.projectId,
  userId: status.userId
});
```

## Best Practices

1. **Debounce Code Changes**
   ```javascript
   const debounce = (func, delay) => {
     let timeout;
     return (...args) => {
       clearTimeout(timeout);
       timeout = setTimeout(() => func(...args), delay);
     };
   };
   
   editor.on('change', debounce((code) => {
     ws.sendCodeChange(fileId, code);
   }, 300)); // Send after 300ms of no changes
   ```

2. **Handle Conflicts**
   - Last-write-wins (simple)
   - Operational Transform (complex, more accurate)
   - Conflict-free Replicated Data Types (CRDT, recommended)

3. **Show User Cursors**
   - Use different colors for each user
   - Display user name next to cursor
   - Update position in real-time

4. **Optimize Messages**
   - Send deltas, not full content (when possible)
   - Batch small changes
   - Compress large messages

5. **Error Handling**
   ```javascript
   ws.onError = (error) => {
     showErrorNotification(`WebSocket error: ${error}`);
     // Retry or fallback to polling
   };
   ```

## REST API Fallbacks

If WebSocket fails, the system falls back to REST API polling:

```javascript
// Fallback: Poll for updates
async function pollForUpdates() {
  const response = await fetch(`/api/v2/session/current?project_id=${projectId}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  return response.json();
}

setInterval(pollForUpdates, 5000); // Poll every 5 seconds
```

## Debugging

Enable debug logging:

```javascript
// Add logging to WebSocket client
const ws = new NexusAIWebSocket({
  // ... other options ...
});

// Wrap send method
const originalSend = ws.send;
ws.send = function(data) {
  console.log('📤 Sending:', data);
  originalSend.call(this, data);
};

// Wrap handler
const originalHandle = ws.handleMessage;
ws.handleMessage = function(message) {
  console.log('📥 Received:', message);
  originalHandle.call(this, message);
};
```

## Performance Considerations

- **Message Size**: Keep payloads under 64KB
- **Frequency**: Don't send more than 100 messages/second
- **Connections**: Plan for 50-100 concurrent users per project
- **Memory**: Each connection uses ~50KB

## Security

- ✅ JWT token authentication required
- ✅ Token verification on connect
- ✅ User isolation (can only edit own projects)
- ✅ Message validation on server
- ✅ No authenticated by-pass

## Future Enhancements

- [ ] CRDT for conflict-free editing
- [ ] Message compression
- [ ] Presence animations
- [ ] Conflict resolution UI
- [ ] Undo/redo with collaboration
- [ ] Code review mode
- [ ] Screen sharing
- [ ] Voice/video chat

## Testing

### Test Local Connection
```bash
# Terminal 1: Start backend
cd backend
uvicorn app.main:app --reload

# Terminal 2: Test with wscat
npm install -g wscat
wscat -c "ws://localhost:8000/ws/project/{project_id}/{user_id}?token={jwt_token}"

# Send test message
> {"type":"ping"}
< {"type":"pong"}
```

### Unit Tests (Frontend)
```javascript
describe('WebSocket Client', () => {
  it('should connect and receive welcome message', async () => {
    const client = new NexusAIWebSocket({ /* ... */ });
    client.connect();
    await new Promise(resolve => client.onConnect = resolve);
    expect(client.isConnected).toBe(true);
  });
});
```

---

**Phase 2B WebSocket Real-Time Features: COMPLETE ✅**

The platform now supports true collaborative editing and real-time updates!
