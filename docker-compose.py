version: '3.8'

services:
  naim-integration:
    build: .
    container_name: uc-intg-naim
    network_mode: host
    volumes:
      - ./config:/config
    environment:
      - UC_CONFIG_HOME=/config
      - UC_INTEGRATION_HTTP_PORT=9090
      - UC_INTEGRATION_INTERFACE=0.0.0.0
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import socket; s=socket.socket(); s.settimeout(5); s.connect(('localhost', 9090)); s.close()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  naim-simulator:
    build: 
      context: .
      dockerfile: Dockerfile.simulator
    container_name: naim-simulator
    ports:
      - "8080:8080"
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    command: ["python", "naim_simulator.py", "--host", "0.0.0.0", "--port", "8080"]