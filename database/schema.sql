CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    user_name VARCHAR(100) NOT NULL UNIQUE,
    user_password VARCHAR(255) NOT NULL,
    avatar_file VARCHAR(255) DEFAULT 'avatar1.png'
);
CREATE TABLE IF NOT EXISTS stories (
    story_id SERIAL PRIMARY KEY,
    owner_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    thumbnail_url TEXT,
    genre VARCHAR(255)
);