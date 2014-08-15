CREATE DATABASE IF NOT EXISTS quarry;
USE quarry;
CREATE TABLE user(
    id INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(255) BINARY NOT NULL UNIQUE,
    wiki_uid INT UNSIGNED NOT NULL UNIQUE
);
CREATE UNIQUE INDEX user_username_index ON user(username);
CREATE UNIQUE INDEX user_wiki_uid ON user(wiki_uid);

CREATE TABLE query(
    id INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNSIGNED NOT NULL,
    title VARCHAR(1024) BINARY,
    latest_rev_id INT UNSIGNED,
    last_touched TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    published SMALLINT DEFAULT 0,
    description TEXT BINARY,
    parent_id INT UNSIGNED
);
CREATE INDEX query_parent_id_index ON query(parent_id);

CREATE TABLE query_revision(
    id INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    text VARCHAR(4096) BINARY NOT NULL,
    query_id INT UNSIGNED NOT NULL,
    latest_run_id INT UNSIGNED,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX query_rev_query_id_index ON query_revision(query_id);

CREATE TABLE query_run(
    id INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    query_rev_id INT UNSIGNED NOT NULL,
    status TINYINT UNSIGNED NOT NULL DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    task_id VARCHAR(36) BINARY,
    extra_info TEXT BINARY,
);
CREATE INDEX query_run_status_index ON query_run(status);

CREATE TABLE star(
    id INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNSIGNED NOT NULL,
    query_id INT UNSIGNED NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX star_user_id_index ON star(user_id);
CREATE INDEX star_query_id_index ON star(query_id);
