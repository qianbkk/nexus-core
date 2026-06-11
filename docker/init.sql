-- Nexus Core Database Initialization
-- Production-ready schema with security and performance optimizations

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types for status fields
CREATE TYPE user_status AS ENUM ('active', 'inactive', 'suspended');
CREATE TYPE workflow_status AS ENUM ('pending', 'running', 'success', 'failed', 'cancelled');
CREATE TYPE audit_action AS ENUM ('CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'ACCESS');

-- Set default privileges for security
ALTER DEFAULT PRIVILEGES REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
ALTER DEFAULT PRIVILEGES REVOKE ALL ON TABLES FROM PUBLIC;

-- Grant permissions to application user (already created by Docker)
GRANT ALL PRIVILEGES ON DATABASE nexus_core TO nexus;

-- Note: Tables will be created by SQLAlchemy migrations
-- This script sets up the database foundation

-- Create index for performance on common queries
-- (Actual tables created by Alembic migrations)

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Nexus Core database initialized successfully';
END $$;
