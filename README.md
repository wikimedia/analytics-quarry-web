# Quarry
[Quarry](https://quarry.wmflabs.org/) is a web service that allows to perform SQL 
queries against Wikipedia and sister projects databases.

## Setting up a local dev environment ##

Quarry uses [Docker](https://docs.docker.com/engine/install/) to set up a local
environment. You can set it up by:

1. [Download](https://docs.docker.com/engine/install/) and install Docker and
   [docker-compose](https://docs.docker.com/compose/) (already ships with docker on Windows and Mac)
3. Clone the [Quarry repository](https://github.com/wikimedia/analytics-quarry-web)
4. Run `docker-compose up`

A web server will be setup, available at http://localhost:5000. Change to python
files will trigger an automatic reload of the server, and your modifications
will imediatelly be taken into account.
A worker node is also created to execute your queries in the background (uses the
same image). Finally, redis and two database instances are also started.

One database is your quarry database the other is a wikireplica-like database
named `mywiki`. This (or `mywiki_p`) is the correct thing to enter in the
database field on all local test queries.

In your local environment, you can query Quarry internal db itself. Use then
"quarry" as database name.

To stop, run `docker-compose stop` or hit CTRL-C on the terminal your docker-compose
is running in. After that, to start with code changes, you'll want to `docker-compose down`
to clean up. Also, this creates a docker volume where sqlite versions of query
results are found. That will not be cleaned up unless you run `docker-compose down -v`


## Running tests ##

If you got things working for the dev environment, this should work well. To run
the tests run:
`docker-compose -f docker-compose-test.yml run --rm  test`

That command will clean up after itself as far as the container goes.

It can also be run with:
`docker-compose -f docker-compose-test.yml run --rm --abort-on-container-exit --exit-code-from test`
but then you should cleanup after by running `docker-compose -f docker-compose-test.yml down -v` to
delete the container.

## Useful commands ##

To pre-compile nunjucks templates:
`nunjucks-precompile quarry/web/static/templates/ > quarry/web/static/templates/compiled.js`

See also commands listed in the mainters documentation:
https://wikitech.wikimedia.org/wiki/Portal:Data_Services/Admin/Quarry
