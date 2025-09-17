# Dockerfile for a Kali-based MCP server with common security tools
FROM kalilinux/kali-rolling

# Avoid interactive prompts during install
ARG DEBIAN_FRONTEND=noninteractive

# Update, install security tools and cleanup
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        python3 python3-pip git curl wget \
        vim nmap netcat-traditional \
        metasploit-framework hydra john \
        sqlmap nikto gobuster wpscan \
    && rm -rf /var/lib/apt/lists/*

    # Install Python dependencies for the MCP server
    RUN pip3 install --no-cache-dir --break-system-packages flask openai

# Copy the server script and expose the service port
COPY server.py /opt/server.py
EXPOSE 5000

ENTRYPOINT ["python3", "/opt/server.py"]
