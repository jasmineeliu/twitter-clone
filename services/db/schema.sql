CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENTION IF NOT EXISTS rum;

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
    withheld_in_countries VARCHAR(2)[]
);

CREATE INDEX idx_users_screen_name ON users(screen_name);
CREATE INDEX ON users(id_users);
CREATE INDEX ON users(name);

-- -- =========================
-- -- CREDENTIALS (REQUIRED ADDITION)
-- -- =========================
 CREATE TABLE credentials (
     id_users BIGINT PRIMARY KEY,
     password TEXT NOT NULL,
     FOREIGN KEY (id_users) REFERENCES users(id_users)
 );

 CREATE INDEX idx_credentials_user ON credentials(id_users);
CREATE INDEX ON credentials(id_users, password);

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
    FOREIGN KEY (id_users) REFERENCES users(id_users)
);

CREATE INDEX ON tweets( id_tweets, id_users, created_at, text);
CREATE INDEX tweets_idx_fts on tweets USING rum(to_tsvector('english', text));

