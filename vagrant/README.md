<!--
#------------------------------------------------------------------------------
#
# Project: PostgreSQL-GeoPackage
# Authors: Stephan Meissl <stephan.meissl@eox.at>
#
#------------------------------------------------------------------------------
# Copyright (C) 2016 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#------------------------------------------------------------------------------
-->

# Vagrant Usage


## How to use Vagrant in a Linux environment

Clone the PostgreSQL-GeoPackage repository:

```sh
git clone git@github.com:EOX-A/PostgreSQL-GeoPackage.git
cd PostgreSQL-GeoPackage/
```

Install VirtualBox & Vagrant. The configuration is tested with:
* [VirtualBox 5.1.2](https://www.virtualbox.org/wiki/Downloads)
* [Vagrant v1.8.5](https://releases.hashicorp.com/vagrant/)

Install Vagrant add-ons:
* `sahara` for [sandboxing](https://github.com/jedi4ever/sahara)
* `vagrant-vbguest` to [check for Virtualbox Guest Additions](https://github.com/dotless-de/vagrant-vbguest)
* `vagrant-cachier` to [cache yum/apt/etc. packages](https://github.com/fgrehm/vagrant-cachier)

```sh
vagrant plugin install sahara
vagrant plugin install vagrant-vbguest
vagrant plugin install vagrant-cachier
```

Run Vagrant:

```sh
cd vagrant/
vagrant up
```

Run scripts:

```sh
vagrant ssh
cd /home/vagrant/PostgreSQL-GeoPackage/
TODO
```

## How to use vagrant in a Windows environment

Use the following steps:

1. Install [Git](http://git-scm.com/download/win)
2. To clone the PostgreSQL-GeoPackage repository start a Git bash and execute the following commands:

    ```sh
    git clone git@github.com:EOX-A/PostgreSQL-GeoPackage.git
    cd PostgreSQL-GeoPackage/
    ```

3. Install [VirtualBox](https://www.virtualbox.org/wiki/Downloads) (tested with version 4.3.0)
4. Install [vagrant](https://www.vagrantup.com/downloads.html) (tested with version 1.3.5)
5. Open the `Vagrantfile` (located in `vagrant/`) with an editor and add the line

    ```sh
    v.customize ["setextradata", :id, "VBoxInternal2/SharedFoldersEnableSymlinksCreate/vagrant", "1"]
    ```

   right before the line

    ```sh
    # Use GUI for debugging purposes
    ```

6. Open an Administrator Console (right click on the command prompt icon and select `Run as administrator`)
7. Enter `secpol.msc` (and hit enter). Navigate to Local Policies, User Rights Assignment and check `Create symbolic links`. Make sure that the Administrator account is added. Close it.
8. Still in the admin console enter `fsutil behavior set SymlinkEvaluation L2L:1 R2R:1 L2R:1 R2L:1` and hit enter. This step isn't necessary on all systems. Only if you use net shares but it does not hurt.
9. Open the Administrative Tools Panel from the Control Panel. Open Component Services.
10. Select Computers, My Computer, Select DCOM Config.
11. Right click on `Virtual Box Application`. Select Security. At `Launch and Activation Permissions` select `Customize`. Hit Edit.
12. Add your user account and Administrator. Select Permissions: Local Launch, Remote Launch, Local Activation and Remote Activation. Hit Ok. And again ok. Close the Component Services.
13. Log off and log on again.
14. To install Vagrant add-ons open an Administrator console and enter:

    ```sh
    vagrant plugin install sahara
    vagrant plugin install vagrant-vbguest
    vagrant plugin install vagrant-cachier
    ```

15. To run Vagrant open an Administrator console and enter:

    ```sh
    cd vagrant/
    vagrant up
    ```

16. To run the scripts open an Administrator console and enter:

    ```sh
    vagrant ssh
    cd /home/vagrant/PostgreSQL-GeoPackage/
    TODO
    ```

## Troubleshoot vagrant

* If the provisioning didn't finish during vagrant up or after changes try: `vagrant provision`
* (Re-)Install virtualbox guest additions in case it complains about not matching versions: `vagrant vbguest -f`
* Slow performance: Check "Enable IO APIC", uncheck "Extended Features: Enable PAE/NX", and uncheck "Enable Nested Paging" in VirtualBox Manager.
* Symlinks with VirtualBox 4.1 not working: vi /opt/vagrant/embedded/gems/gems/vagrant-1.3.5/plugins/providers/virtualbox/driver/version_4_1.rb and add those changes: https://github.com/mitchellh/vagrant/commit/387692f9c8fa4031050646e2773b3d2d9b2c994e
