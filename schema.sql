CREATE TABLE IF NOT EXISTS guild (
    "id" BIGINT,
    "prefix" VARCHAR(32) DEFAULT '^^',
    "mute_role" BIGINT,
    "allow_global_bans" BOOLEAN DEFAULT FALSE,
    "language" VARCHAR DEFAULT 'en'
);

CREATE TABLE IF NOT EXISTS logging (
    "guild_id" BIGINT,
    "channel_id" BIGINT UNIQUE,
    "log_types" VARCHAR[]
)