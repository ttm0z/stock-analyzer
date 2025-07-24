# Redis Installation and Setup Guide

## Prerequisites

This stock analyzer application uses Redis for caching stock data, search results, and improving performance. Follow these steps to install and configure Redis properly.

## 1. Install Redis Server

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install redis-server
```

### Fedora
```bash
sudo dnf install redis
sudo systemctl enable redis
sudo systemctl start redis
```

### macOS (using Homebrew)
```bash
brew install redis
```

### Docker (Alternative)
```bash
docker pull redis:7-alpine
```

## 2. Install Python Redis Package

Add Redis to your Python environment:

```bash
pip install redis>=4.0.0
```

Or if using the requirements.txt:
```bash
pip install -r requirements.txt
```

## 3. Configure Redis

### Option A: Use Project Configuration (Recommended)

The project includes a secure Redis configuration file at `backend/app/redis.conf`. Start Redis with this configuration:

```bash
cd backend
redis-server app/redis.conf
```

### Option B: Manual Configuration

If you prefer to configure Redis manually, edit `/etc/redis/redis.conf`:

```conf
# Bind to localhost only for security
bind 127.0.0.1

# Set the port (default is fine)
port 6379

# Enable password authentication
requirepass 7nU4pIfCGUyqb08dyd55VF3z5QAZmPOG

# Memory management
maxmemory 512mb
maxmemory-policy allkeys-lru

# Enable persistence
save 900 1
save 300 10
save 60 10000

appendonly yes
appendfsync everysec

# Security
protected-mode yes
```

## 4. Environment Configuration

Ensure your `.env` file contains the Redis configuration:

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=7nU4pIfCGUyqb08dyd55VF3z5QAZmPOG
REDIS_MAX_CONNECTIONS=50
CACHE_DEFAULT_TTL=300
CACHE_KEY_PREFIX=stock_app
```

## 5. Start Redis

### Using Project Configuration
```bash
cd backend
redis-server app/redis.conf
```

### Using System Service (Fedora)
```bash
# Redis should already be running if you followed the Fedora install steps
sudo systemctl status redis  # Check status
sudo systemctl restart redis # Restart if needed
```

### Using Docker
```bash
docker run -d \
  --name redis-stock-analyzer \
  -p 6379:6379 \
  -v $(pwd)/backend/app/redis.conf:/usr/local/etc/redis/redis.conf \
  redis:7-alpine \
  redis-server /usr/local/etc/redis/redis.conf
```

## 6. Verify Installation

### Test Redis Connection
```bash
cd backend
python test_redis.py
```

### Manual Testing
```bash
redis-cli -a 7nU4pIfCGUyqb08dyd55VF3z5QAZmPOG
> ping
PONG
> set test "Hello Redis"
OK
> get test
"Hello Redis"
> exit
```

## 7. Start the Application

### Option 1: Standard Start
```bash
cd backend
python run.py
```

### Option 2: Secure Start (Recommended)
```bash
cd backend
python start_secure.py
```

This will automatically:
- Start Redis with the secure configuration
- Initialize the database
- Start the Flask application

## 8. Monitor Cache Performance

Access the admin interface to monitor Redis performance:

- **Cache Statistics**: `http://localhost:5000/api/admin/cache/stats`
- **Health Check**: `http://localhost:5000/api/admin/health`
- **Clear Cache**: `http://localhost:5000/api/admin/cache/clear`

## 9. Docker Compose (Alternative Setup)

If you prefer using Docker Compose, use the included configuration:

```bash
cd backend/app
docker-compose up -d redis
```

This includes Redis Commander for GUI administration at `http://localhost:8081`.

## Troubleshooting

### Redis Connection Errors
- Verify Redis is running: `sudo systemctl status redis`
- Check the password in `.env` matches Redis configuration
- Ensure Redis is binding to the correct interface

### Permission Errors
- Make sure Redis has proper file permissions for data directory
- Check SELinux settings on Fedora: `sudo setsebool -P redis_enable_notify on`
- If SELinux is blocking Redis: `sudo semanage port -a -t redis_port_t -p tcp 6379`

### Memory Issues
- Adjust `maxmemory` in Redis configuration based on your system
- Monitor memory usage with `redis-cli info memory`

### Port Conflicts
- Ensure port 6379 is not used by other services
- Change port in both Redis config and `.env` if needed

## Cache Configuration

The application uses intelligent caching with different TTL values:

- **Real-time quotes**: 60 seconds
- **Search results**: 5 minutes  
- **Company profiles**: 1 hour
- **Financial statements**: 24 hours
- **Historical data**: 1 hour
- **Market news**: 5 minutes

## Security Notes

- Redis is configured to bind only to localhost (127.0.0.1)
- Password authentication is enabled
- Protected mode is active
- Change the default password in production environments
- Consider using Redis AUTH and SSL/TLS for production deployments

## Production Considerations

- Use Redis Sentinel or Cluster for high availability
- Enable SSL/TLS encryption
- Set up proper backup strategies for Redis data
- Monitor Redis performance and memory usage
- Consider using Redis on a separate server for scalability