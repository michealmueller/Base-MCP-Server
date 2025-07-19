# Postman Collection Setup Guide

## 📋 Overview

This guide will help you set up and use the **Daggerheart MCP Server** Postman collection to test your MCP server endpoints and tools.

## 🚀 Quick Start

### 1. Import the Collection

1. Open **Postman**
2. Click **Import** button
3. Select the file: `Daggerheart_MCP_Server.postman_collection.json`
4. The collection will be imported with all endpoints and examples

### 2. Configure Environment Variables

The collection uses these variables (already configured):

- **`base_url`**: `http://localhost:8001` (MCP server URL)
- **`server_host`**: `localhost` (Server hostname)
- **`server_port`**: `8001` (Server port)

### 3. Start Your MCP Server

```bash
# In your project directory
cd /home/mmueller/avworx/daggerheart/agent
source .venv/bin/activate
python -m mcp_server.main --debug --port 8001
```

## 📚 Collection Structure

### **Server Info** 📊
- **Get Server Info**: Basic server information
- **Health Check**: Server health and status
- **API Documentation**: Interactive Swagger UI

### **Tools** 🛠️
- **List Available Tools**: Get all available tools with metadata

### **Tool Execution** ⚡
- **Get Current Time**: Execute time tool
- **Search Web**: Execute search tool
- **File Operations - List Directory**: List files
- **File Operations - Read File**: Read file contents
- **File Operations - Write File**: Write to file

### **WebSocket** 🔌
- **WebSocket Connection**: Real-time communication endpoint

### **Error Examples** ❌
- **Invalid Tool Name**: Error handling example
- **Invalid Method**: Method validation example

## 🧪 Testing Your Tools

### Test 1: Server Health
1. Run **"Health Check"** request
2. Verify response shows `"status": "healthy"`

### Test 2: List Tools
1. Run **"List Available Tools"** request
2. Verify you see all 3 tools: `get_current_time`, `search_web`, `file_operations`

### Test 3: Execute Tools
1. Run **"Get Current Time"** - should return current timestamp
2. Run **"Search Web"** - should return search results
3. Run **"File Operations - List Directory"** - should list current directory

## 🔧 Customization

### Add New Tools
To test new tools you add to the server:

1. **Create new request** in "Tool Execution" folder
2. **Set method** to `POST`
3. **Set URL** to `{{base_url}}/execute`
4. **Set headers**: `Content-Type: application/json`
5. **Set body** (raw JSON):
```json
{
  "id": "your-request-id",
  "method": "tools/call",
  "params": {
    "name": "your_tool_name",
    "arguments": {
      "param1": "value1",
      "param2": "value2"
    }
  }
}
```

### Environment Variables
You can create different environments for:
- **Development**: `http://localhost:8001`
- **Staging**: `http://staging-server:8001`
- **Production**: `http://production-server:8001`

## 📊 Response Examples

### Successful Tool Execution
```json
{
  "id": "request-id",
  "result": "tool output here",
  "error": null
}
```

### Error Response
```json
{
  "id": "request-id",
  "result": null,
  "error": {
    "code": -32603,
    "message": "Tool 'tool_name' not found"
  }
}
```

## 🎯 Best Practices

1. **Test Health First**: Always check server health before testing tools
2. **Use Descriptive IDs**: Use meaningful request IDs for easier debugging
3. **Validate Responses**: Check both success and error scenarios
4. **Monitor Performance**: Use Postman's response time tracking
5. **Document Changes**: Update collection when adding new tools

## 🔗 Related Resources

- [Postman Collections Documentation](https://learning.postman.com/docs/collections/use-collections/create-collections/)
- [MCP Server Documentation](./README.md)
- [API Documentation](./docs/api.md)

## 🆘 Troubleshooting

### Common Issues

**Server Not Running**
- Error: `ECONNREFUSED`
- Solution: Start the MCP server first

**Tool Not Found**
- Error: `Tool 'tool_name' not found`
- Solution: Check tool name spelling, ensure tool is registered

**Invalid JSON**
- Error: `400 Bad Request`
- Solution: Validate JSON syntax in request body

**WebSocket Issues**
- Error: `404 Not Found` on WebSocket
- Solution: Install `websockets` package: `pip install websockets`

## 📈 Next Steps

1. **Automate Testing**: Use Postman's collection runner for automated testing
2. **Performance Testing**: Use Newman CLI for load testing
3. **Integration**: Connect your AI agent to the MCP server
4. **Monitoring**: Set up monitoring for production deployment

---

**Happy Testing! 🎉** 