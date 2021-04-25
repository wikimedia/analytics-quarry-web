# Quarry
[Quarry](https://quarry.wmflabs.org/) is a web service that allows to perform SQL 
queries against Wikipedia and sister projects databases.

## Setting up a local testing environment ##

Quarry uses [Docker](https://docs.docker.com/engine/install/) to set up a local
environment. You can set it up by:

1. [Download](https://docs.docker.com/engine/install/) and install Docker and
   docker-compose (ship with the first on Windows)
3. Clone the [Quarry repository](https://github.com/wikimedia/analytics-quarry-web)
4. Run `docker-compose up`

A web server will be setup, available at http://localhost:5000. Change to python
files will trigger an automatic reload of the server, and your modifications
will imediatelly be taken into account.
A worker node is also created to execute your queries in the background (uses the
same image). Finally, redis and database instances are also started.

In your local environment, you can query Quarry internal db itself. Use then
"quarry" as database name.

To stop, run `docker-compose stop`.

## Useful commands ##

To pre-compile nunjucks templates:
`nunjucks-precompile quarry/web/static/templates/ > quarry/web/static/templates/compiled.js`

To update requirements.txt with later versions:
`pipenv lock -r > requirements.txt`

See also commands listed in the mainters documentation:
https://wikitech.wikimedia.org/wiki/Portal:Data_Services/Admin/Quarry