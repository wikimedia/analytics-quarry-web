#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import logging
import re
import sys
from typing import Optional

import pymysql
from pymysql.cursors import Cursor
import yaml


BATCH_SIZE = 300


def extract_dbnames(qtext: str, qdb: str, regex, db_regex) -> Optional[str]:
    """
    Attempt to determine the database we are running against from table names.
    Only one database should be accepted. If multiples are given, assume this is
    invalid.
    """
    if qdb:
        # The DB is already set.
        return None

    if qtext.count("use ") > 1 or qtext.count("USE ") > 1:
        return None

    qchunks = qtext.split()
    dotted_chunks = [x for x in qchunks if "." in x]
    match_r = regex.match(qtext)
    if len(dotted_chunks) < 1:
        # Then we have a single database query against enwiki or using "use"
        if match_r:
            if db_regex.match(match_r.group("db")):
                return match_r.group("db")

        return "enwiki_p"
    suspected_dbs = [x.split(".")[0] for x in dotted_chunks]
    dbs = [x for x in suspected_dbs if db_regex.match(x)]

    if not all(db == dbs[0] for db in dbs):
        return None

    if match_r:
        # If we have specific DB names against tables and a use statement,
        # they must match, or we give up.
        if match_r.group("db") != dbs[0]:
            return None

    return dbs[0]


def write_execute(cursor: Cursor, query: str, dry_run: bool = False, *args) -> None:
    """Do operation or simulate
    :param cursor: Cursor
    :param query: str
    :param dry_run: bool
    """
    logging.debug("SQL: %s, %s", query, args)
    if not dry_run:
        cursor.execute(query, args)


def main() -> None:
    argparser = argparse.ArgumentParser(
        "multiinstance_migration",
        description=(
            "Bring the database into a state that works better with "
            "multiinstance"
        ),
    )

    argparser.add_argument(
        "--config",
        help="Path to find the configuration file",
        default="../quarry/config.yaml",
    )
    argparser.add_argument(
        "--dry-run",
        help=(
            "Give this parameter if you don't want the script to actually"
            " make changes."
        ),
        action="store_true",
    )
    argparser.add_argument(
        "--debug",
        help=("Turn on maximum verbosity."),
        action="store_true",
    )

    args = argparser.parse_args()

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s",
        level=logging.DEBUG if args.dry_run or args.debug else logging.INFO,
    )
    with open(args.config, "r") as conf_file:
        try:
            config = yaml.safe_load(conf_file)
        except yaml.YAMLError as exc:
            logging.error(exc)
            sys.exit(2)

    conn = pymysql.connect(
        user=config["DB_USER"],
        passwd=config["DB_PASSWORD"],
        host=config["DB_HOST"],
        database=config["DB_NAME"],
        charset="utf8",
    )
    with conn.cursor() as cursor:
        cursor.execute("SET NAMES 'utf8';")
        cursor.execute("SET SESSION innodb_lock_wait_timeout=1;")
        cursor.execute("SET SESSION lock_wait_timeout=60;")

        write_execute(
            cursor,
            (
                "ALTER TABLE query_revision ADD COLUMN IF NOT EXISTS "
                "query_database VARCHAR(66) NULL;"
            ),
            args.dry_run,
        )
        conn.commit()
        cursor.execute("SELECT id, text, query_database from query_revision;")
        queries = cursor.fetchmany(BATCH_SIZE)
        db_regex = re.compile(r"^(?:(?:centralauth|meta|[a-z]*wik[a-z]+)(?:_p)?)?$")
        regex = re.compile(r"(use|USE)\s+(?P<db>\w+)\s*;")
        while queries:
            for q_id, text, query_database in queries:  # type: ignore[misc]
                db_name = extract_dbnames(text, query_database, regex, db_regex)
                if db_name:
                    update = """
                    UPDATE query_revision SET query_database = %s WHERE id = %s
                    """
                    write_execute(cursor, update, args.dry_run, db_name, q_id)
                    conn.commit()

            queries = cursor.fetchmany(BATCH_SIZE)


if __name__ == "__main__":
    main()
