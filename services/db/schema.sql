CREATE EXTENSION IF NOT EXISTS postgis;

-- =========================
-- USERS
-- =========================
CREATE TABLE users (
    id_users BIGINT PRIMARY KEY,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    friends_count INTEGER,
    listed_count INTEGER,
    favourites_count INTEGER,
    statuses_count INTEGER,
    protected BOOLEAN,
    verified BOOLEAN,
    screen_name TEXT,
    name TEXT,
    location TEXT,
    description TEXT,
    withheld_in_countries VARCHAR(2)[],
);

-- CREATE INDEX idx_users_screen_name ON users(screen_name);


-- -- =========================
-- -- CREDENTIALS (REQUIRED ADDITION)
-- -- =========================
-- CREATE TABLE credentials (
--     id_users BIGINT PRIMARY KEY REFERENCES users(id_users),
--     password_hash TEXT NOT NULL,
-- );

-- CREATE INDEX idx_credentials_user ON credentials(id_users);


-- =========================
-- TWEETS
-- =========================
CREATE TABLE tweets (
    id_tweets BIGINT PRIMARY KEY,
    id_users BIGINT,
    created_at TIMESTAMPTZ,
    in_reply_to_status_id BIGINT,
    quoted_status_id BIGINT,
    retweet_count SMALLINT,
    favorite_count SMALLINT,
    quote_count SMALLINT,
    withheld_copyright BOOLEAN,
    withheld_in_countries VARCHAR(2)[],
    source TEXT,
    text TEXT,
    country_code VARCHAR(2),
    state_code VARCHAR(2),
    lang TEXT,
    place_name TEXT,
    FOREIGN KEY (id_users) REFERENCES users(id_users),
);

CREATE INDEX ON tweets (id_tweets, lang);
CREATE INDEX ON tweets
USING GIN (to_tsvector('english', text))
WHERE lang = 'en';
