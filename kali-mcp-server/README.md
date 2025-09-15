# Kali MCP Server

This directory provides a self-contained Docker setup for a Kali Linux
container exposing a very small **MCP**-style server. The image installs
several common penetration-testing tools and runs a Flask endpoint that
executes commands supplied via JSON.

> ⚠️ **Use only on systems you are authorized to test. Misuse may be
> illegal.**

## Build

```bash
docker build -t kali-mcp-server .
```

## Run

```bash
docker run -it --rm -p 5000:5000 kali-mcp-server
```

## Example Request

```bash
curl -X POST http://localhost:5000/run \
     -H "Content-Type: application/json" \
     -d '{"cmd": "nmap --help"}'
```

Adjust the installed packages or server logic as needed for your use
case.
