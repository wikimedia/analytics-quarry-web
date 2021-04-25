import pymysql


class ReplicaConnectionException(Exception):
    pass


class Replica:
    def __init__(self, config):
        self.config = config
        self.dbname = ""

    def _db_name_mangler(self):
        if self.dbname == "":
            raise ReplicaConnectionException(
                "Attempting connection before a database is selected"
            )

        # Special case for docker development setup where connexion is made to
        # "db" container and "quarry" database
        from .app import app  # here to avoid cyclyc import
        if app.config['DEBUG'] and self.dbname == "quarry":
            self.database_name = "db"
            self.database_p = "quarry"
        elif self.dbname == "meta" or self.dbname == "meta_p":
            self.database_name = "s7"
            self.database_p = "meta_p"
        elif self.dbname == "centralauth" or self.dbname == "centralauth_p":
            self.database_name = "s7"
            self.database_p = "centralauth_p"
        else:
            self.database_name = (
                self.dbname
                if not self.dbname.endswith("_p")
                else self.dbname[:-2]
            )
            self.database_p = (
                self.dbname
                if self.dbname.endswith("_p")
                else "{}_p".format(self.dbname)
            )

    @property
    def connection(self):
        self._replica.ping(reconnect=True)
        return self._replica

    @connection.setter
    def connection(self, db):
        if db == self.dbname and hasattr(self, "_replica"):
            return self._replica.ping(reconnect=True)  # Reuse connections

        if hasattr(self, "_replica"):
            if self._replica.open:
                self._replica.close()

        self.dbname = db
        self._db_name_mangler()
        self._replica = pymysql.connect(
            host="{}.{}".format(
                self.database_name, self.config["REPLICA_DOMAIN"]
            ),
            db=self.database_p,
            user=self.config["REPLICA_USER"],
            passwd=self.config["REPLICA_PASSWORD"],
            port=self.config["REPLICA_PORT"],
            charset="utf8",
            client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS,
        )

    @connection.deleter
    def connection(self):
        self.dbname = ""
        if hasattr(self, "_replica"):
            if self._replica.open:
                self._replica.close()

            delattr(self, "_replica")
