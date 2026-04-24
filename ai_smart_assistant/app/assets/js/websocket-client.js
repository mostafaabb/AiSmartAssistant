/**
 * NexusAI WebSocket Client
 * Real-time collaboration library for the NexusAI platform
 *
 * Usage:
 *
 * const client = new NexusAIWebSocket({
 *   projectId: 'project-uuid',
 *   userId: 'user-uuid',
 *   token: 'jwt-token',
 *   onConnect: () => console.log('Connected!')
 * });
 *
 * client.connect();
 *
 * // Send code change
 * client.sendCodeChange('file-id', 'new code content');
 *
 * // Send cursor position
 * client.sendCursorMove(10, 5); // line 10, column 5
 *
 * // Send chat message
 * client.sendChatMessage('Hello team!');
 */

export class NexusAIWebSocket {
  constructor(options) {
    this.projectId = options.projectId;
    this.userId = options.userId;
    this.token = options.token;
    this.baseUrl = options.baseUrl || `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`;

    // Callbacks
    this.onConnect = options.onConnect || (() => {});
    this.onDisconnect = options.onDisconnect || (() => {});
    this.onMessage = options.onMessage || (() => {});
    this.onError = options.onError || (() => {});
    this.onCodeChange = options.onCodeChange || (() => {});
    this.onCursorMove = options.onCursorMove || (() => {});
    this.onChatMessage = options.onChatMessage || (() => {});
    this.onPresence = options.onPresence || (() => {});
    this.onExecutionOutput = options.onExecutionOutput || (() => {});

    this.ws = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
    this.reconnectDelay = options.reconnectDelay || 3000;
    this.heartbeatInterval = null;
  }

  /**
   * Connect to WebSocket server
   */
  connect() {
    const url = `${this.baseUrl}/ws/project/${this.projectId}/${this.userId}?token=${this.token}`;

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('✅ WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.onConnect();

        // Start heartbeat ping
        this.startHeartbeat();
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (e) {
          console.error('Failed to parse message:', e);
        }
      };

      this.ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        this.onError(error);
      };

      this.ws.onclose = () => {
        console.log('🔌 WebSocket closed');
        this.isConnected = false;
        this.clearHeartbeat();
        this.onDisconnect();

        // Attempt reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff
          console.log(`⏳ Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
          setTimeout(() => this.connect(), delay);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      this.onError(error);
    }
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect() {
    this.clearHeartbeat();
    if (this.ws) {
      this.ws.close();
    }
  }

  /**
   * Handle incoming message
   */
  handleMessage(message) {
    this.onMessage(message);

    const type = message.type;

    switch (type) {
      case 'connected':
        console.log('✅ Connected to project:', message.project_id);
        break;

      case 'code_change':
        this.onCodeChange(message.data);
        break;

      case 'cursor_move':
        this.onCursorMove(message.data);
        break;

      case 'chat_message':
        this.onChatMessage(message.data);
        break;

      case 'presence':
        this.onPresence(message.data);
        break;

      case 'execution_output':
        this.onExecutionOutput(message.data);
        break;

      case 'pong':
        // Heartbeat response
        break;

      case 'error':
        console.error('Server error:', message.message);
        break;

      default:
        console.warn('Unknown message type:', type);
    }
  }

  /**
   * Send code change
   */
  sendCodeChange(fileId, content, delta = null) {
    this.send({
      type: 'code_change',
      file_id: fileId,
      content: content,
      delta: delta,
    });
  }

  /**
   * Send cursor position
   */
  sendCursorMove(line, column) {
    this.send({
      type: 'cursor_move',
      line: line,
      column: column,
    });
  }

  /**
   * Send chat message
   */
  sendChatMessage(content) {
    this.send({
      type: 'chat_message',
      content: content,
    });
  }

  /**
   * Send execution result (from code runner)
   */
  sendExecutionResult(executionId, output, error = null, status = 'success') {
    this.send({
      type: 'execution_result',
      execution_id: executionId,
      output: output,
      error: error,
      status: status,
    });
  }

  /**
   * Send raw message
   */
  send(data) {
    if (!this.isConnected) {
      console.warn('WebSocket not connected');
      return;
    }

    try {
      this.ws.send(JSON.stringify(data));
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  }

  /**
   * Start heartbeat ping
   */
  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected) {
        this.send({ type: 'ping' });
      }
    }, 30000); // Ping every 30 seconds
  }

  /**
   * Clear heartbeat
   */
  clearHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Get connection status
   */
  getStatus() {
    return {
      connected: this.isConnected,
      projectId: this.projectId,
      userId: this.userId,
    };
  }
}

export default NexusAIWebSocket;
