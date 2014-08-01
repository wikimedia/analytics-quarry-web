def check_sql(sql):
    """Check if given SQL is ok to execute.
    Super minimal and stupid right now, and should never
    be considered 'authoritative'. Will probably always be
    easily cirumventible by dedicated trolls, but should keep
    the merely clueless out"""
    if 'information_schema' in sql.lower():
        # According to springle hitting this db can fuck
        # things up for everyone, and it isn't easy to
        # restrict access to this from mysql
        return ("Hitting information_schema", "Unauthorized access to restricted database")
    return True
