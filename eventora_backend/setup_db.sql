-- ─────────────────────────────────────────────────────────────────────────────
-- Eventora MySQL Setup Script
-- Run this ONCE before starting the Django server.
-- Usage: mysql -u root -p < setup_db.sql
-- ─────────────────────────────────────────────────────────────────────────────

-- 1. Create the database
CREATE DATABASE IF NOT EXISTS eventora_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- 2. Create a dedicated application user (recommended for production)
--    Replace 'your_password' with a strong password.
CREATE USER IF NOT EXISTS 'eventora_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON eventora_db.* TO 'eventora_user'@'localhost';
FLUSH PRIVILEGES;

-- 3. Confirm
SHOW DATABASES LIKE 'eventora_db';
