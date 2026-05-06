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

    geo geometry
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


-- =========================
-- TWEET URLS
-- =========================
CREATE TABLE tweet_urls (
    id_tweets BIGINT REFERENCES tweets(id_tweets) ON DELETE CASCADE,
    urls TEXT NOT NULL
);

CREATE INDEX idx_tweet_urls_tweet ON tweet_urls(id_tweets);


-- =========================
-- MENTIONS
-- =========================
CREATE TABLE tweet_mentions (
    id_tweets BIGINT REFERENCES tweets(id_tweets) ON DELETE CASCADE,
    id_users BIGINT REFERENCES users(id_users) ON DELETE CASCADE
);

CREATE INDEX idx_tweet_mentions_tweet ON tweet_mentions(id_tweets);
CREATE INDEX idx_tweet_mentions_user ON tweet_mentions(id_users);


-- =========================
-- TAGS
-- =========================
CREATE TABLE tweet_tags (
    id_tweets BIGINT REFERENCES tweets(id_tweets) ON DELETE CASCADE,
    tag TEXT NOT NULL
);

CREATE INDEX idx_tweet_tags_tag ON tweet_tags(tag);
CREATE INDEX idx_tweet_tags_tweet ON tweet_tags(id_tweets);
CREATE INDEX idx_tweet_tags_tag_tweet ON tweet_tags(tag, id_tweets);


-- =========================
-- MEDIA
-- =========================
CREATE TABLE tweet_media (
    id_tweets BIGINT REFERENCES tweets(id_tweets) ON DELETE CASCADE,
    urls TEXT,
    type TEXT
);

CREATE INDEX idx_tweet_media_tweet ON tweet_media(id_tweets);


-- =========================
-- MATERIALIZED VIEWS
-- =========================

CREATE MATERIALIZED VIEW tweet_tags_total AS
SELECT
    row_number() OVER (ORDER BY count(*) DESC) AS row,
    tag,
    count(*) AS total
FROM tweet_tags
GROUP BY tag
ORDER BY total DESC;

CREATE MATERIALIZED VIEW tweet_tags_cooccurrence AS
SELECT
    t1.tag AS tag1,
    t2.tag AS tag2,
    count(*) AS total
FROM tweet_tags t1
JOIN tweet_tags t2 ON t1.id_tweets = t2.id_tweets
GROUP BY t1.tag, t2.tag
ORDER BY total DESC;
