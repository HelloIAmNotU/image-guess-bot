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