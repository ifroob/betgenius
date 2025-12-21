# BetGenius - Deployment Guide

Complete guide for deploying BetGenius in various environments.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Production Deployment](#production-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Environment Configuration](#environment-configuration)
7. [Monitoring & Logs](#monitoring--logs)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+), macOS 11+, or Windows 10+
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 5GB free space
- **Network**: Open ports 3000, 8001, 27017

### Software Requirements

- **Python**: 3.10 or higher
- **Node.js**: 18.x or higher
- **MongoDB**: 6.0 or higher
- **Yarn**: 1.22.x or higher
- **Git**: 2.x or higher

---

## Local Development

### Step 1: Clone & Setup

```bash
# Clone repository
git clone <repository-url>
cd betgenius

# Verify structure
ls -la
# Should see: backend/, frontend/, README.md, etc.
```

### Step 2: Setup MongoDB

```bash
# Ubuntu/Debian
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod

# macOS
brew tap mongodb/brew
brew install mongodb-community@6.0
brew services start mongodb-community@6.0

# Verify
mongosh --eval "db.version()"
```

### Step 3: Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Configure environment
cat > .env << EOF
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="*"
EOF

# Start server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Backend URL**: http://localhost:8001

### Step 4: Setup Frontend

Open a new terminal:

```bash
cd frontend

# Install dependencies
yarn install

# Configure environment
cat > .env << EOF
REACT_APP_BACKEND_URL=http://localhost:8001
WDS_SOCKET_PORT=443
ENABLE_HEALTH_CHECK=false
EOF

# Start development server
yarn start
```

**Frontend URL**: http://localhost:3000

### Step 5: Verify Installation

```bash
# Test backend
curl http://localhost:8001/api/models

# Test frontend
curl http://localhost:3000

# Check MongoDB
mongosh
use test_database
db.models.find()
```

---

## Production Deployment

### Environment Setup

#### Backend Production `.env`

```env
MONGO_URL="mongodb://production-host:27017"
DB_NAME="betgenius_production"
CORS_ORIGINS="https://yourdomain.com"
```

#### Frontend Production `.env`

```env
REACT_APP_BACKEND_URL=https://api.yourdomain.com
WDS_SOCKET_PORT=443
ENABLE_HEALTH_CHECK=true
```

### Backend Production Build

```bash
cd backend

# Install production dependencies only
pip install -r requirements.txt --no-dev

# Use production ASGI server
pip install gunicorn

# Run with Gunicorn
gunicorn server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8001 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

### Frontend Production Build

```bash
cd frontend

# Build for production
yarn build

# Serve with a static file server
npm install -g serve
serve -s build -l 3000

# Or use nginx (recommended)
sudo apt-get install nginx
sudo cp build/* /var/www/html/
```

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/betgenius

# Frontend
server {
    listen 80;
    server_name yourdomain.com;
    
    root /var/www/html;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
}

# Backend API
server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/betgenius /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL/HTTPS Setup (Let's Encrypt)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get SSL certificates
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

---

## Docker Deployment

### Dockerfile for Backend

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Dockerfile for Frontend

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine as build

WORKDIR /app

COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

COPY . .
RUN yarn build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  mongodb:
    image: mongo:6.0
    container_name: betgenius-mongo
    ports:
      - "27017:27017"
    volumes:
      - mongo-data:/data/db
    environment:
      MONGO_INITDB_DATABASE: test_database

  backend:
    build: ./backend
    container_name: betgenius-backend
    ports:
      - "8001:8001"
    environment:
      MONGO_URL: mongodb://mongodb:27017
      DB_NAME: test_database
      CORS_ORIGINS: "*"
    depends_on:
      - mongodb

  frontend:
    build: ./frontend
    container_name: betgenius-frontend
    ports:
      - "3000:3000"
    environment:
      REACT_APP_BACKEND_URL: http://localhost:8001
    depends_on:
      - backend

volumes:
  mongo-data:
```

### Running with Docker

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up -d --build
```

---

## Kubernetes Deployment

### Backend Deployment

```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: betgenius-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: betgenius-backend
  template:
    metadata:
      labels:
        app: betgenius-backend
    spec:
      containers:
      - name: backend
        image: betgenius/backend:latest
        ports:
        - containerPort: 8001
        env:
        - name: MONGO_URL
          valueFrom:
            secretKeyRef:
              name: betgenius-secrets
              key: mongo-url
        - name: DB_NAME
          value: "test_database"
        - name: CORS_ORIGINS
          value: "*"
---
apiVersion: v1
kind: Service
metadata:
  name: betgenius-backend-service
spec:
  selector:
    app: betgenius-backend
  ports:
  - protocol: TCP
    port: 8001
    targetPort: 8001
  type: LoadBalancer
```

### Frontend Deployment

```yaml
# k8s/frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: betgenius-frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: betgenius-frontend
  template:
    metadata:
      labels:
        app: betgenius-frontend
    spec:
      containers:
      - name: frontend
        image: betgenius/frontend:latest
        ports:
        - containerPort: 3000
        env:
        - name: REACT_APP_BACKEND_URL
          value: "http://backend-service:8001"
---
apiVersion: v1
kind: Service
metadata:
  name: betgenius-frontend-service
spec:
  selector:
    app: betgenius-frontend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 3000
  type: LoadBalancer
```

### MongoDB StatefulSet

```yaml
# k8s/mongodb-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongodb
spec:
  serviceName: mongodb
  replicas: 1
  selector:
    matchLabels:
      app: mongodb
  template:
    metadata:
      labels:
        app: mongodb
    spec:
      containers:
      - name: mongodb
        image: mongo:6.0
        ports:
        - containerPort: 27017
        volumeMounts:
        - name: mongo-storage
          mountPath: /data/db
  volumeClaimTemplates:
  - metadata:
      name: mongo-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: mongodb
spec:
  selector:
    app: mongodb
  ports:
  - protocol: TCP
    port: 27017
  clusterIP: None
```

### Deploy to Kubernetes

```bash
# Apply configurations
kubectl apply -f k8s/mongodb-statefulset.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

# Check status
kubectl get pods
kubectl get services

# View logs
kubectl logs -f deployment/betgenius-backend
kubectl logs -f deployment/betgenius-frontend
```

---

## Supervisor Deployment (Current Setup)

### Supervisor Configuration

The application uses Supervisor for process management in containerized environments.

#### Backend Configuration

```ini
# /etc/supervisor/conf.d/backend.conf
[program:backend]
command=/root/.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1 --reload
directory=/app/betgenius/backend
autostart=true
autorestart=true
environment=APP_URL="https://your-app.preview.emergentagent.com"
stderr_logfile=/var/log/supervisor/backend.err.log
stdout_logfile=/var/log/supervisor/backend.out.log
stopsignal=TERM
stopwaitsecs=30
stopasgroup=true
```

#### Frontend Configuration

```ini
# /etc/supervisor/conf.d/frontend.conf
[program:frontend]
command=yarn start
environment=HOST="0.0.0.0",PORT="3000"
directory=/app/betgenius/frontend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/frontend.err.log
stdout_logfile=/var/log/supervisor/frontend.out.log
stopsignal=TERM
stopwaitsecs=50
stopasgroup=true
```

### Supervisor Commands

```bash
# Reload configuration
supervisorctl reread
supervisorctl update

# Start services
supervisorctl start backend
supervisorctl start frontend
supervisorctl start all

# Stop services
supervisorctl stop backend
supervisorctl stop frontend
supervisorctl stop all

# Restart services
supervisorctl restart backend
supervisorctl restart frontend
supervisorctl restart all

# Check status
supervisorctl status

# View logs
tail -f /var/log/supervisor/backend.*.log
tail -f /var/log/supervisor/frontend.*.log
```

---

## Environment Configuration

### Development vs Production

| Setting | Development | Production |
|---------|-------------|------------|
| **Backend Port** | 8001 | 8001 (behind proxy) |
| **Frontend Port** | 3000 | 80/443 (nginx) |
| **MongoDB** | localhost:27017 | Replica set |
| **CORS** | `*` | Specific domain |
| **Debug** | Enabled | Disabled |
| **Hot Reload** | Enabled | Disabled |
| **Logging** | Console | File + monitoring |
| **SSL** | Not required | Required |

### Environment Variables Best Practices

```bash
# Use environment-specific files
.env.development
.env.production
.env.staging

# Never commit .env files to git
echo ".env*" >> .gitignore

# Use secret management in production
# - AWS Secrets Manager
# - HashiCorp Vault
# - Kubernetes Secrets
```

---

## Monitoring & Logs

### Application Logs

#### Backend Logs

```bash
# Development
# View in terminal where uvicorn is running

# Production with Supervisor
tail -f /var/log/supervisor/backend.err.log
tail -f /var/log/supervisor/backend.out.log

# Production with systemd
journalctl -u betgenius-backend -f

# Docker
docker logs -f betgenius-backend

# Kubernetes
kubectl logs -f deployment/betgenius-backend
```

#### Frontend Logs

```bash
# Development
# View in terminal where yarn start is running
# Also check browser console (F12)

# Production with Supervisor
tail -f /var/log/supervisor/frontend.err.log

# Docker
docker logs -f betgenius-frontend

# Kubernetes
kubectl logs -f deployment/betgenius-frontend
```

### MongoDB Logs

```bash
# Ubuntu/Debian
sudo tail -f /var/log/mongodb/mongod.log

# macOS
tail -f /usr/local/var/log/mongodb/mongo.log

# Docker
docker logs -f betgenius-mongo
```

### Health Checks

#### Backend Health Check

```bash
# Manual check
curl http://localhost:8001/docs

# Automated monitoring
curl http://localhost:8001/api/models
```

#### Frontend Health Check

```bash
# Manual check
curl http://localhost:3000

# Check if React app loads
curl -I http://localhost:3000
```

#### MongoDB Health Check

```bash
# Connection check
mongosh --eval "db.adminCommand('ping')"

# Performance check
mongosh --eval "db.serverStatus()"
```

### Performance Monitoring

#### Backend Metrics

```python
# Add to server.py
from fastapi import Request
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

#### Frontend Metrics

```javascript
// Add to App.js
import { useEffect } from 'react';

useEffect(() => {
  // Log page load time
  window.addEventListener('load', () => {
    const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
    console.log(`Page load time: ${loadTime}ms`);
  });
}, []);
```

---

## Troubleshooting

### Common Issues

#### 1. Backend Won't Start

**Symptom**: Backend service fails immediately

**Diagnosis**:
```bash
# Check logs
tail -f /var/log/supervisor/backend.err.log

# Common errors:
# - ModuleNotFoundError
# - MongoDB connection refused
# - Port already in use
```

**Solutions**:
```bash
# Install missing dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Check MongoDB
sudo systemctl status mongodb
sudo systemctl start mongodb

# Check port availability
lsof -i :8001
kill -9 <PID>
```

#### 2. Frontend Won't Start

**Symptom**: Frontend fails to start or shows blank page

**Diagnosis**:
```bash
# Check logs
tail -f /var/log/supervisor/frontend.err.log

# Common errors:
# - Module not found
# - EADDRINUSE (port in use)
# - Backend URL incorrect
```

**Solutions**:
```bash
# Reinstall dependencies
cd frontend
rm -rf node_modules yarn.lock
yarn install

# Check port
lsof -i :3000
kill -9 <PID>

# Verify backend URL
cat .env
# Should match actual backend location
```

#### 3. MongoDB Connection Failed

**Symptom**: `pymongo.errors.ServerSelectionTimeoutError`

**Solutions**:
```bash
# Check MongoDB status
sudo systemctl status mongodb

# Restart MongoDB
sudo systemctl restart mongodb

# Check connection string
mongosh "mongodb://localhost:27017"

# Check firewall
sudo ufw status
sudo ufw allow 27017
```

#### 4. CORS Errors

**Symptom**: Browser console shows CORS policy errors

**Solutions**:
```bash
# Backend .env
CORS_ORIGINS="http://localhost:3000"
# Or for development:
CORS_ORIGINS="*"

# Restart backend
supervisorctl restart backend
```

#### 5. API Returns 404

**Symptom**: All API calls return 404 Not Found

**Diagnosis**:
```bash
# Check backend is running
curl http://localhost:8001/docs

# Should see Swagger UI
```

**Solutions**:
```bash
# Verify API prefix in requests
# All endpoints should use /api prefix
curl http://localhost:8001/api/models  # ✓
curl http://localhost:8001/models      # ✗

# Check frontend .env
REACT_APP_BACKEND_URL=http://localhost:8001
```

### Performance Issues

#### Slow API Response

```bash
# Check MongoDB indexes
mongosh
use test_database
db.models.getIndexes()
db.journal.getIndexes()

# Create indexes if needed
db.journal.createIndex({ "created_at": -1 })
db.models.createIndex({ "model_type": 1 })
```

#### High Memory Usage

```bash
# Check process memory
ps aux | grep -E "uvicorn|node"

# Backend: Reduce workers
# In supervisor config:
command=/root/.venv/bin/uvicorn server:app --workers 1

# Frontend: Build for production
cd frontend
yarn build
# Serve build/ instead of dev server
```

---

## Backup & Recovery

### Database Backup

```bash
# Full backup
mongodump --db=test_database --out=/backup/$(date +%Y%m%d)

# Restore
mongorestore --db=test_database /backup/20231221/test_database

# Automated daily backups
crontab -e
# Add:
0 2 * * * mongodump --db=test_database --out=/backup/$(date +\%Y\%m\%d)
```

### Application Backup

```bash
# Backup configuration
tar -czf betgenius-config-$(date +%Y%m%d).tar.gz \
  backend/.env \
  frontend/.env \
  /etc/supervisor/conf.d/backend.conf \
  /etc/supervisor/conf.d/frontend.conf

# Backup code
git push origin main  # Use version control!
```

---

## Security Checklist

### Pre-Production Security

- [ ] Change default MongoDB credentials
- [ ] Enable MongoDB authentication
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS/SSL
- [ ] Set proper CORS origins (not `*`)
- [ ] Enable rate limiting
- [ ] Implement authentication
- [ ] Update all dependencies
- [ ] Enable security headers
- [ ] Configure firewall rules
- [ ] Implement input validation
- [ ] Enable logging and monitoring
- [ ] Regular security audits
- [ ] Backup strategy in place

---

## Scaling Strategy

### Horizontal Scaling

```bash
# Kubernetes: Scale replicas
kubectl scale deployment betgenius-backend --replicas=5
kubectl scale deployment betgenius-frontend --replicas=3

# Docker Compose: Scale services
docker-compose up -d --scale backend=3 --scale frontend=2
```

### Load Balancing

```nginx
# Nginx load balancer
upstream backend {
    server localhost:8001;
    server localhost:8002;
    server localhost:8003;
}

server {
    location /api {
        proxy_pass http://backend;
    }
}
```

### Database Scaling

```bash
# MongoDB replica set
mongosh
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongo1:27017" },
    { _id: 1, host: "mongo2:27017" },
    { _id: 2, host: "mongo3:27017" }
  ]
})
```

---

## Rollback Strategy

### Quick Rollback

```bash
# Git rollback
git log --oneline
git checkout <previous-commit-hash>
supervisorctl restart all

# Docker rollback
docker-compose down
docker-compose up -d <previous-image-tag>

# Kubernetes rollback
kubectl rollout undo deployment/betgenius-backend
kubectl rollout undo deployment/betgenius-frontend
```

---

<div align="center">
  <p>🚀 Ready for deployment!</p>
  <p>For support, check logs and refer to troubleshooting section</p>
</div>
