FROM python:3.11-slim

WORKDIR /app

COPY mcp_server/requirements.txt .
RUN pip install -r requirements.txt

COPY mcp_server/ ./mcp_server/

EXPOSE 8000

CMD ["python", "-m", "mcp_server.main", "--host", "0.0.0.0"]