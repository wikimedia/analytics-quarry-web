## Setting up a local environment ##

Quarry uses [Vagrant](https://www.vagrantup.com/) to set up a local environment.
You can set it up by:

1. [Download](https://www.vagrantup.com/downloads.html) and install Vagrant
2. Download and install [VirtualBox](https://www.virtualbox.org/)
3. Clone the [Quarry repository](https://github.com/wikimedia/analytics-quarry-web)
4. Run `vagrant up`
5. Access your local quarry instance on `localhost:5000`

The default instance queries the quarry database itself :)

### Reloading after making a change ###

The dev setups are set up to use auto-reloading when any files are changed. If that does not work well, you can reload them manually by:

1. Run `vagrant ssh`
2. Run `sudo service quarry-* restart`

This will restart both the web server and the celery worker nodes.
