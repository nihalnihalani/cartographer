# Cartographer on Cloud Run: ADK web UI serving both agents.
# Node.js is required because all database access goes through the official
# MongoDB MCP server (`npx mongodb-mcp-server`) as a stdio subprocess.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Pre-bake the MCP server so cold starts don't wait on npx downloads.
RUN npm install -g mongodb-mcp-server

COPY agents/ agents/

ENV PORT=8080
CMD ["sh", "-c", "adk web agents --host 0.0.0.0 --port ${PORT}"]
