atg-minimongo
=============

This repository implements a lightweight ORM for interfacing efficiently and easily with MongoDB. The binding is done using `pymongo` under the hood, and allows recursive attribute style indexing for convenience.

### Setup ###

This package was built using `setuptools` in Python > 3.4 and is not entirely backwards compatible with Python 2.7. Setup of the package for development or for production use is relatively straightforward.

Everything below is written for Ubuntu 14.04.

#### Python 3 ####

Get the latest version of Python 3 provided by Ubuntu 14.04.

```
# System dependencies
sudo apt-get install build-essential libssl-dev libffi-dev

# Get or update system provided Python 3
sudo apt-get update
sudo apt-get install python python-dev python3 python3-dev
wget https://bootstrap.pypa.io/get-pip.py
sudo python get-pip.py
rm get-pip.py

# Setup pip, virtualenv, and virtualenvwrapper
sudo pip install --upgrade pip
sudo pip install https://github.com/pypa/virtualenv/tarball/develop
sudo pip install virtualenvwrapper
echo -e "\n# virtualenv config\nexport WORKON_HOME=$HOME/.virtualenvs\nsource /usr/local/bin/virtualenvwrapper.sh\n" >> ~/.bashrc

# Setup a new virtual environment for Python 3
mkvirtualenv -p python3 atg
deactivate
workon atg
```

#### Package ####

Clone the repository into a convenient directory.
```
git clone git@code.espn.com:ATG/atg-minimongo.git atg-minimongo
cd atg-minimongo
```

Setup and expose the package with `python setup.py develop`.

```
python setup.py develop
```

Note that `python setup.py develop` will only symlink to your local repository directory, so any code changes should be reflected immediately in the package. This avoids having to run `python setup.py install` every time code is changed (which would be annoying, and might also have other complications).

Test the package with `python setup.py test`.

```
python setup.py test
```

This runs the tests in the [tests](./tests) directory, ensuring that binding works with your local MongoDB. You will need to add the following user with readWrite access to a database which will be created and used during testing, and dropped afterward.

```js
db.createUser({
    'user': 'atgminimongoTester',
    'pwd': 'atgminimongoTester',
    'roles':[
        {'role': 'readWrite', 'db': 'atgminimongo_testing'}
    ]
})
```
