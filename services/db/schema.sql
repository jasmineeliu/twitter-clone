CREATE EXTENSION IF NOT EXISTS postgis;

-- =========================
-- USERS
-- =========================
CREATE TABLE users (
    id_users BIGINT PRIMARY KEY,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    urls TEXT,
    friends_count INTEGER CHECK (friends_count >= 0),
    listed_count INTEGER CHECK (listed_count >= 0),
    favourites_count INTEGER CHECK (favourites_count >= 0),
    statuses_count INTEGER CHECK (statuses_count >= 0),
    protected BOOLEAN DEFAULT FALSE,
    verified BOOLEAN DEFAULT FALSE,
    screen_name TEXT UNIQUE,
    name TEXT,
    location TEXT,
    description TEXT,
    withheld_in_countries VARCHAR(2)[]
);

CREATE INDEX idx_users_screen_name ON users(screen_name);


-- =========================
-- CREDENTIALS (REQUIRED ADDITION)
-- =========================
CREATE TABLE credentials (
    id_users BIGINT PRIMARY KEY REFERENCES users(id_users) ON DELETE CASCADE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_credentials_user ON credentials(id_users);


-- =========================
-- TWEETS
-- =========================
CREATE TABLE tweets (
    id_tweets BIGINT PRIMARY KEY,
    id_users BIGINT REFERENCES users(id_users) ON DELETE CASCADE,

    created_at TIMESTAMPTZ,

    in_reply_to_status_id BIGINT,
    in_reply_to_user_id BIGINT,

    quoted_status_id BIGINT,

    retweet_count INTEGER DEFAULT 0,
    favorite_count INTEGER DEFAULT 0,
    quote_count INTEGER DEFAULT 0,

    withheld_copyright BOOLEAN,
    withheld_in_countries VARCHAR(2)[],

    source TEXT,
    text TEXT NOT NULL,

    country_code VARCHAR(2),
    state_code VARCHAR(2),
    lang TEXT,

    place_name TEXT,

    -- geo geometry
);

-- Core query indexes
CREATE INDEX idx_tweets_user ON tweets(id_users);
CREATE INDEX idx_tweets_created_at ON tweets(created_at);
CREATE INDEX idx_tweets_lang ON tweets(lang);
CREATE INDEX idx_tweets_reply ON tweets(in_reply_to_status_id);
CREATE INDEX idx_tweets_quote ON tweets(quoted_status_id);

-- Full-text search (important for feed/search endpoints)
CREATE INDEX idx_tweets_fts
ON tweets
USING GIN (to_tsvector('english', text))
WHERE lang = 'en';
