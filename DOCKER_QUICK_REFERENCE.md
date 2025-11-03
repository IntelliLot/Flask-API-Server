# 🐳 Docker Quick Reference

## One-Command Start

```bash
# Interactive start
./start.sh

# Or directly:
./docker-helper.sh dev-start   # Development (Port 5001)
./docker-helper.sh prod-start  # Production (Port 80)
```

---

## 🎯 Quick Commands

### Development
```bash
./docker-helper.sh dev-start      # Start
./docker-helper.sh dev-stop       # Stop
./docker-helper.sh dev-logs       # View logs
./docker-helper.sh dev-restart    # Restart
./docker-helper.sh dev-shell      # Open shell
```

### Production
```bash
./docker-helper.sh prod-start     # Start
./docker-helper.sh prod-stop      # Stop
./docker-helper.sh prod-logs      # View logs
./docker-helper.sh prod-restart   # Restart
./docker-helper.sh prod-shell     # Open shell
```

### Database
```bash
./docker-helper.sh db-backup      # Backup MongoDB
./docker-helper.sh db-restore backup.gz  # Restore
```

### Utility
```bash
./docker-helper.sh status         # Show status
./docker-helper.sh clean          # Remove everything
```

---

## 🌐 Access URLs

### Development (Port 5001)
- **Application**: http://localhost:5001
- **API Health**: http://localhost:5001/health
- **MongoDB**: mongodb://localhost:27017
- **Mongo Express**: http://localhost:8081 (admin/admin123)

### Production (Port 80)
- **Application**: http://localhost:80
- **API Health**: http://localhost:80/health
- **MongoDB**: mongodb://localhost:27017

---

## 📁 Environment Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables (edit this!) |
| `gcs-credentials.json` | Google Cloud Storage credentials |

---

## 🔧 Configuration

### Port Settings (.env)
```bash
# Development
FLASK_PORT=5001
FLASK_DEBUG=True

# Production
FLASK_PORT=80
FLASK_DEBUG=False
```

### MongoDB (.env)
```bash
MONGODB_URI=mongodb://mongodb:27017/
MONGODB_DB_NAME=parking_detection

# Production - add authentication
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=your-secure-password
```

### Google Cloud Storage (.env)
```bash
GCS_BUCKET_NAME=your-bucket-name
GCS_CREDENTIALS_PATH=./gcs-credentials.json
GCS_ENABLE=true
```

---

## 🚀 First Time Setup

```bash
# 1. Create .env file
cp .env.example .env
nano .env

# 2. Add GCS credentials (if using cloud storage)
# Place gcs-credentials.json in project root

# 3. Start development
./docker-helper.sh dev-start

# 4. Verify
curl http://localhost:5001/health
```

---

## 📊 Monitoring

```bash
# Container stats
docker stats

# View logs
./docker-helper.sh dev-logs   # Development
./docker-helper.sh prod-logs  # Production

# Check status
./docker-helper.sh status
```

---

## 🐛 Common Issues

### Port Already in Use
```bash
# Find process
sudo lsof -i :5001
sudo lsof -i :80

# Kill process
sudo kill -9 <PID>
```

### Can't Connect to MongoDB
```bash
# Check if running
docker ps | grep mongodb

# Restart
./docker-helper.sh dev-restart
```

### Permission Denied
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

---

## 🧹 Cleanup

```bash
# Remove everything (containers, volumes, images)
./docker-helper.sh clean

# Or manually
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.prod.yml down -v
```

---

## 📚 Full Documentation

See **[DOCKER_DEPLOYMENT_GUIDE.md](DOCKER_DEPLOYMENT_GUIDE.md)** for complete documentation.
