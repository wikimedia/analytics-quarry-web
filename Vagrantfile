# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "debian/stretch64"

  config.vm.provision "shell", path: 'provision.bash'

  # Port for the python webservice
  config.vm.network "forwarded_port", guest: 5000, host: 5000

  # config.vm.synced_folder './', '/vagrant', type: 'rsync'

  config.vm.provider :virtualbox do |v|
    v.memory = 1024
  end
  config.vm.provider :libvirt do |v|
    v.memory = 1024
  end
end
