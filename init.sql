# init.sql
-- Create database and user if they don't exist
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_files_user_id ON files(user_id);
CREATE INDEX IF NOT EXISTS idx_files_created_at ON files(created_at);
CREATE INDEX IF NOT EXISTS idx_file_shares_file_id ON file_shares(file_id);
CREATE INDEX IF NOT EXISTS idx_file_shares_shared_with_user_id ON file_shares(shared_with_user_id);
CREATE INDEX IF NOT EXISTS idx_file_shares_expires_at ON file_shares(expires_at);