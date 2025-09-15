-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS soc_agent;

-- Create user if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'soc_agent') THEN
        CREATE ROLE soc_agent LOGIN PASSWORD 'soc_agent_password';
    END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE soc_agent TO soc_agent;
