CREATE TABLE cards (
    card_id TEXT PRIMARY KEY, 
    user_id BIGINT
);

CREATE TABLE cardcounts (
    cardname TEXT PRIMARY KEY, 
    cardnum INT
);

CREATE TABLE timeout (
    user_id BIGINT PRIMARY KEY,
    dropped_time BIGINT
);

CREATE TABLE channels (
    server_id BIGINT PRIMARY KEY,
    channel_id BIGINT
);