# Security through Obscurity: GenAI-based Defensive Cybersecurity

This is the GitHub repository for my master thesis Security through Obscurity: GenAI-based Defensive Cybersecurity at the University of Zurich. This repository is a prototye for a secure obfuscated
database system augmented with SIEM-based monitoring and alerting.

## Features

- Frontend interface for legitimate user interaction
- Data obfuscation to transform real data rows
- Syntheic data generation
- Stores obfuscated real and synthetic data in ramdomized order, where only the backend identifier can maintain the mapping
- Database logging and Elastic Stack alerting

## Installation

### Prerequisites

```bash
pip install -r requirements.txt
```

### Steps

1. Set Up Docker Containers

```bash
cd app/docker
docker-compose up -d
```

This will start all containers in the background. Wait a few minutes for all services to initialize, especially Elasticsearch which may take 1-2 minutes.

2. Set Up PostgreSQL JDBC Driver for Logstash

Logstash needs the PostgreSQL JDBC driver to read audit logs from the database.

```bash
bash setup_jdbc_driver.sh
```
This will download the PostgreSQL JDBC driver (version 42.7.1) to `app/docker/logstash/jdbc/`.

3. Set Up Frontend

```bash
cd app/frontend
npm install
```

For user management, follow [USER_MANAGEMENT_GUIDE.md](USER_MANAGEMENT_GUIDE.md)

4. Start Backend Server

```bash
cd app
source .venv/bin/activate
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at:
- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

5. Start Fronend Server

In a new terminal window:

```bash
cd app/frontend
npm run serve
```

The frontend will be available at:
- **Frontend**: http://localhost:3000

### Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Use the user account created in Step 3|
| **Backend API** | http://localhost:8000 | N/A |
| **API Docs** | http://localhost:8000/docs | N/A |
| **Kibana** | http://localhost:5601 | N/A |
| **pgAdmin** | http://localhost:8080 | Email: `admin@example.com`, Password: `admin123` |
| **Elasticsearch** | http://localhost:9200 | N/A |


### Next Steps

1. Upload csv file from the frontend interface, sample uplaod files can be found at [dataset](app/backend/evaluation/eval_dataset/).

2. Set database audit triggers following [AUDIT_TRIGGERS_GUIDE.md](AUDIT_TRIGGERS_GUIDE.md)

3. Set Kibana alerts following [KIBANA_ALERT_GUIDE.md](KIBANA_ALERT_GUIDE.md)

## Stopping the System

### Stop Frontend and Backend

Press `CTRL+C` in the terminal windows running the frontend and backend servers.

### Stop Docker Containers

```bash
cd app/docker
docker-compose down
```

