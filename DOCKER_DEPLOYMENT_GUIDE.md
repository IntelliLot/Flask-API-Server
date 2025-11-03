# 🐳 Docker Deployment Guide

## Overview

This project includes complete Docker configuration for both **Development** and **Production** environments.

---

## 📋 Quick Start

### Development (Port 5001)
```bash
# Start development environment
./docker-helper.sh dev-start

# View logs
./docker-helper.sh dev-logs

# Stop
./docker-helper.sh dev-stop
```

### Production (Port 80)
```bash
# Start production environment
./docker-helper.sh prod-start

# View logs
./docker-helper.sh prod-logs

# Stop
./docker-helper.sh prod-stop
```

---

## 🏗️ Architecture

### Development Setup
- **Flask App**: Port 5001, hot-reload enabled
- **MongoDB**: Port 27017
- **Mongo Express**: Port 8081 (admin/admin123)
- **Volumes**: Source code mounted for live updates

### Production Setup
- **Flask App**: Port 80, Gunicorn with 4 workers
- **MongoDB**: Port 27017, authentication enabled
- **Nginx**: Port 443 (optional, for SSL)
- **Volumes**: Only data directories mounted

---

## 📁 Docker Files

| File | Purpose |
|------|---------|
| `Dockerfile` | Base image for development |
| `Dockerfile.dev` | Development-optimized image with hot reload |
| `Dockerfile.prod` | Production-optimized image with Gunicorn |
| `docker-compose.yml` | Default compose (development) |
| `docker-compose.dev.yml` | Development environment |
| `docker-compose.prod.yml` | Production environment |
| `.dockerignore` | Files to exclude from build |
| `docker-helper.sh` | Helper script for common commands |

---

## 🚀 Detailed Setup

### Prerequisites

### 1. Install Docker & Docker Compose
   ```bash
   # Ubuntu/Debian
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   
   # Docker Compose is included with Docker Desktop
   # For Linux server, install the plugin:
   sudo apt-get install docker-compose-plugin
   
   # Verify
   docker --version
   docker compose version
   ```

2. **Configure Environment Variables**
   ```bash
   # Create .env file (if not exists)
   cp .env.example .env
   
   # Edit .env with your settings
   nano .env
   ```

3. **Add GCS Credentials (Optional)**
   ```bash
   # Place your GCS credentials file
   cp /path/to/your/gcs-credentials.json ./gcs-credentials.json
   chmod 600 gcs-credentials.json
   ```

---

## 🛠️ Development Environment

### Start Development
```bash
./docker-helper.sh dev-start
```

**Services:**
- 🌐 **Application**: http://localhost:5001
- 🗄️ **MongoDB**: mongodb://localhost:27017
- 📊 **Mongo Express**: http://localhost:8081

### Features
- ✅ Hot reload on code changes
- ✅ Source code mounted as volume
- ✅ Flask debug mode enabled
- ✅ Mongo Express for database GUI

### Common Commands
```bash
# View logs
./docker-helper.sh dev-logs

# Restart
./docker-helper.sh dev-restart

# Open shell in container
./docker-helper.sh dev-shell

# Rebuild image
./docker-helper.sh build-dev

# Stop
./docker-helper.sh dev-stop
```

### Manual Docker Compose
```bash
# Start
docker compose -f docker-compose.dev.yml up -d

# Stop
docker compose -f docker-compose.dev.yml down

# View logs
docker compose -f docker-compose.dev.yml logs -f app
```

---

## 🏭 Production Environment

### Start Production
```bash
./docker-helper.sh prod-start
```

**Services:**
- 🌐 **Application**: http://localhost:80
- 🗄️ **MongoDB**: mongodb://localhost:27017 (with auth)

### Features
- ✅ Gunicorn WSGI server (4 workers)
- ✅ Non-root user for security
- ✅ Health checks enabled
- ✅ Resource limits configured
- ✅ Log rotation enabled
- ✅ Optimized multi-stage build

### Environment Variables
```bash
# Production-specific variables in .env
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_PORT=80
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=your-secure-password
```

### Common Commands
```bash
# View logs
./docker-helper.sh prod-logs

# Restart
./docker-helper.sh prod-restart

# Open shell in container
./docker-helper.sh prod-shell

# Rebuild image
./docker-helper.sh build-prod

# Stop
./docker-helper.sh prod-stop
```

### Manual Docker Compose
```bash
# Start
docker compose -f docker-compose.prod.yml up -d

# Stop
docker compose -f docker-compose.prod.yml down

# View logs
docker compose -f docker-compose.prod.yml logs -f app
```

---

## 💾 Database Operations

### Backup Database
```bash
./docker-helper.sh db-backup
```
Creates backup file: `mongodb-backup/backup_YYYYMMDD_HHMMSS.gz`

### Restore Database
```bash
./docker-helper.sh db-restore mongodb-backup/backup_20251102_143052.gz
```

### Manual Backup/Restore
```bash
# Backup
docker compose -f docker-compose.prod.yml exec mongodb \
    mongodump --archive --gzip > backup.gz

# Restore
cat backup.gz | docker compose -f docker-compose.prod.yml exec -T mongodb \
    mongorestore --archive --gzip
```

---

## 🔧 Configuration

### Port Configuration

**Development (.env):**
```bash
FLASK_PORT=5001
```

**Production (.env):**
```bash
FLASK_PORT=80
```

### Resource Limits (Production)

Edit `docker-compose.prod.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '1.0'
      memory: 2G
```

### MongoDB Authentication (Production)

```bash
# In .env
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=your-secure-password-here
```

---

## 🌐 Nginx Reverse Proxy (Optional)

For HTTPS support, uncomment the nginx service in `docker-compose.prod.yml`.

### Create nginx.conf
```nginx
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:80;
    }

    server {
        listen 443 ssl;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### Add SSL Certificates
```bash
mkdir -p ssl
# Copy your SSL certificates
cp /path/to/cert.pem ssl/
cp /path/to/key.pem ssl/
```

---

## 📊 Monitoring

### View Status
```bash
./docker-helper.sh status
```

### View Logs
```bash
# Development
./docker-helper.sh dev-logs

# Production
./docker-helper.sh prod-logs

# Specific service
docker compose -f docker-compose.prod.yml logs -f mongodb
```

### Container Stats
```bash
docker stats
```

### Health Checks
```bash
# Check app health
curl http://localhost:5001/health  # Development
curl http://localhost:80/health    # Production
```

---

## 🧹 Cleanup

### Remove Everything
```bash
./docker-helper.sh clean
```

This removes:
- All containers
- All volumes
- All networks
- All images

### Remove Specific Environment
```bash
# Development
docker compose -f docker-compose.dev.yml down -v

# Production
docker compose -f docker-compose.prod.yml down -v
```

### Remove Images Only
```bash
docker compose -f docker-compose.prod.yml down --rmi all
```

---

## 🐛 Troubleshooting

### Problem: Port Already in Use

**Solution:**
```bash
# Check what's using the port
sudo lsof -i :5001
sudo lsof -i :80

# Kill the process
sudo kill -9 <PID>

# Or change port in .env
FLASK_PORT=5002
```

### Problem: Permission Denied

**Solution:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Or run with sudo
sudo ./docker-helper.sh dev-start
```

### Problem: Container Keeps Restarting

**Solution:**
```bash
# Check logs
docker logs parking-detection-prod

# Check if .env is correct
cat .env

# Ensure MongoDB is ready
docker compose -f docker-compose.prod.yml up mongodb
```

### Problem: Can't Connect to MongoDB

**Solution:**
```bash
# Check if MongoDB is running
docker ps | grep mongodb

# Check connection
docker compose -f docker-compose.prod.yml exec mongodb mongosh

# Check environment variables
docker compose -f docker-compose.prod.yml exec app env | grep MONGO
```

### Problem: GCS Upload Fails

**Solution:**
```bash
# Check if credentials exist
ls -la gcs-credentials.json

# Check if it's mounted
docker compose -f docker-compose.prod.yml exec app ls -la gcs-credentials.json

# Verify environment variables
docker compose -f docker-compose.prod.yml exec app env | grep GCS
```

---

## 🚀 Deployment to Cloud

### Google Cloud Platform (GCP)

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash

# Authenticate
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Build and push image
docker tag parking-detection:prod gcr.io/YOUR_PROJECT_ID/parking-detection:latest
docker push gcr.io/YOUR_PROJECT_ID/parking-detection:latest

# Deploy to Cloud Run
gcloud run deploy parking-detection \
    --image gcr.io/YOUR_PROJECT_ID/parking-detection:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars "$(cat .env | tr '\n' ',' | sed 's/,$//')"
```

### AWS EC2

```bash
# SSH to EC2 instance
ssh -i key.pem ubuntu@your-ec2-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Clone repository
git clone https://github.com/IntelliLot/Flask-API-Server.git
cd Flask-API-Server

# Configure .env
nano .env

# Start production
./docker-helper.sh prod-start
```

### DigitalOcean

Similar to AWS EC2 deployment.

---

## 📈 Performance Optimization

### 2. Use Docker Build Cache
```bash
# Build with cache
docker compose -f docker-compose.prod.yml build

# Build without cache (clean build)
docker compose -f docker-compose.prod.yml build --no-cache
```

### 2. Optimize Image Size
- Multi-stage builds (already implemented)
- Use Alpine base images (optional)
- Remove unnecessary packages

### 3. Scale Services
```bash
# Scale app to 3 instances
docker compose -f docker-compose.prod.yml up -d --scale app=3
```

---

## 🔒 Security Best Practices

1. ✅ **Non-root user** in production (implemented)
2. ✅ **Health checks** enabled
3. ✅ **Resource limits** configured
4. ✅ **Secrets management** via .env
5. ✅ **MongoDB authentication** in production
6. ⚠️ **Use HTTPS** in production (configure nginx)
7. ⚠️ **Regular updates** of base images
8. ⚠️ **Scan images** for vulnerabilities

```bash
# Scan image for vulnerabilities
docker scout cves parking-detection:prod
```

---

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Compose V2](https://docs.docker.com/compose/compose-v2/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [MongoDB Docker Hub](https://hub.docker.com/_/mongo)

---

## 🎯 Summary

✅ **Development**: Port 5001, hot reload, debug mode  
✅ **Production**: Port 80, Gunicorn, optimized  
✅ **Helper Script**: Easy management with `docker-helper.sh`  
✅ **Database**: Automatic backup/restore  
✅ **Scalable**: Ready for cloud deployment  
✅ **Secure**: Non-root user, health checks, resource limits  

Your Docker setup is production-ready! 🎉
