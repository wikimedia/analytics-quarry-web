# Quarry
[Quarry](https://quarry.wmcloud.org/) is a web service that allows to perform SQL 
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


### Updating existing containers ###

If you had already run a dev environment (that is, ran `docker-compose up`) you might want to update
the containers with the new dependencies by running `docker-compose build` before running
`docker-compose up` again.


## Running tests ##

1. Set up [Blubber](https://wikitech.wikimedia.org/wiki/Blubber) to run tests:
https://wikitech.wikimedia.org/wiki/Blubber/Download
```bash
blubber() {
  if [ $# -lt 2 ]; then
    echo 'Usage: blubber config.yaml variant'
    return 1
  fi
  curl -s -H 'content-type: application/yaml' --data-binary @"$1" https://blubberoid.wikimedia.org/v1/"$2"
}
```
2. Run tests:
`blubber .pipeline/blubber.yaml quarry-test | docker build --tag blubber-quarry:01 --file - . ; docker run blubber-quarry:01`


## Useful commands ##

To pre-compile nunjucks templates:
`nunjucks-precompile quarry/web/static/templates/ > quarry/web/static/templates/compiled.js`

See also commands listed in the mainters documentation:
https://wikitech.wikimedia.org/wiki/Portal:Data_Services/Admin/Quarry
