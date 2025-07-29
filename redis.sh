#!/bin/bash

# Redis Management Script for Container Environment
# Usage: ./redis.sh [start|stop|restart|status|test]

case "$1" in
    start)
        echo "Starting Redis server..."
        # Try multiple methods to start Redis
        if redis-server --daemonize yes; then
            echo "Redis started successfully with daemonize"
        elif redis-server /etc/redis/redis.conf --daemonize yes 2>/dev/null; then
            echo "Redis started with config file"
        elif nohup redis-server > /dev/null 2>&1 & then
            echo "Redis started with nohup"
        else
            echo "Failed to start Redis"
            exit 1
        fi
        ;;
    
    stop)
        echo "Stopping Redis server..."
        redis-cli shutdown
        pkill redis-server
        echo "Redis stopped"
        ;;
    
    restart)
        echo "Restarting Redis..."
        $0 stop
        sleep 2
        $0 start
        ;;
    
    status)
        echo "Checking Redis status..."
        if redis-cli ping > /dev/null 2>&1; then
            echo "✅ Redis is running"
            redis-cli info server | grep redis_version
        else
            echo "❌ Redis is not running"
        fi
        ;;
    
    test)
        echo "Testing Redis connection..."
        if redis-cli ping; then
            echo "✅ Redis connection successful"
            echo "Setting test key..."
            redis-cli set test_key "Hello Redis"
            echo "Getting test key..."
            redis-cli get test_key
            echo "Deleting test key..."
            redis-cli del test_key
        else
            echo "❌ Redis connection failed"
        fi
        ;;
    
    logs)
        echo "Redis logs (if available)..."
        tail -f /var/log/redis/redis-server.log 2>/dev/null || echo "No log file found"
        ;;
    
    config)
        echo "Redis configuration info..."
        redis-cli config get "*"
        ;;
    
    *)
        echo "Redis Management Script"
        echo "Usage: $0 {start|stop|restart|status|test|logs|config}"
        echo ""
        echo "Commands:"
        echo "  start   - Start Redis server"
        echo "  stop    - Stop Redis server"
        echo "  restart - Restart Redis server"
        echo "  status  - Check if Redis is running"
        echo "  test    - Test Redis functionality"
        echo "  logs    - Show Redis logs"
        echo "  config  - Show Redis configuration"
        echo ""
        echo "Quick commands:"
        echo "  redis-cli ping           # Test connection"
        echo "  redis-cli info           # Server info"
        echo "  redis-cli monitor        # Monitor commands"
        echo "  redis-cli --help         # Redis CLI help"
        exit 1
        ;;
esac