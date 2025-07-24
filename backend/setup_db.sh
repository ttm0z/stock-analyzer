#!/bin/bash
# Database Setup Script
echo "🗄️ Setting up PostgreSQL..."

# Create user and database
sudo -u postgres psql -c "CREATE USER stockuser WITH PASSWORD 'sasfcUlSi_jLh68ZwnRPRBNowlvpJrPY';"
sudo -u postgres psql -c "CREATE DATABASE stockdb OWNER stockuser;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE stockdb TO stockuser;"

echo "✅ Database setup complete!"
