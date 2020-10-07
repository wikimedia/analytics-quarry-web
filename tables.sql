CREATE DATABASE IF NOT EXISTS quarry CHARACTER SET utf8;
USE quarry;
CREATE TABLE IF NOT EXISTS user(
    id INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(255) BINARY NOT NULL UNIQUE,
    wiki_uid INT UNSIGNED NOT NULL UNIQUE
);
CREATE UNIQUE INDEX IF NOT EXISTS user_username_index ON user( username);
CREATE UNIQUE INDEX IF NOT EXISTS user_wiki_uid ON user(wiki_uid);

CREATE TABLE IF NOT EXISTS user_group(
    id INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNSIGNED NOT NULL,
    group_name VARCHAR(255) BINARY NOT NULL
);
CREATE INDEX IF NOT EXISTS user_group_user_group_index ON user_group(user_id, group_name);
CREATE INDEX IF NOT EXISTS user_group_user_id_index ON user_group(user_id);
CREATE INDEX IF NOT EXISTS user_group_group_name_index ON user_group(group_name);

CREATE TABLE IF NOT EXISTS query(
    id INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNSIGNED NOT NULL,
    title VARCHAR(1024) BINARY,
    latest_rev_id INT UNSIGNED,
    last_touched TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    published SMALLINT DEFAULT 0 NOT NULL,
    description TEXT BINARY,
    parent_id INT UNSIGNED
);
CREATE INDEX IF NOT EXISTS query_parent_id_index ON query(parent_id);

CREATE TABLE IF NOT EXISTS query_revision(
    id INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    text TEXT BINARY NOT NULL,
    query_database VARCHAR(1024) BINARY,
    query_id INT UNSIGNED NOT NULL,
    latest_run_id INT UNSIGNED,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS query_rev_query_id_index ON query_revision(query_id);

CREATE TABLE IF NOT EXISTS query_run(
    id INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    query_rev_id INT UNSIGNED NOT NULL,
    status TINYINT UNSIGNED NOT NULL DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    task_id VARCHAR(36) BINARY,
    extra_info TEXT BINARY
);
CREATE INDEX IF NOT EXISTS query_run_status_index ON query_run(status);

CREATE TABLE IF NOT EXISTS star(
    id INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNSIGNED NOT NULL,
    query_id INT UNSIGNED NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS star_user_id_index ON star(user_id);
CREATE INDEX IF NOT EXISTS star_query_id_index ON star(query_id);
CREATE UNIQUE INDEX IF NOT EXISTS star_user_query_index ON star(user_id, query_id);
