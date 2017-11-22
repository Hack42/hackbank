# hackbank

The hackbank consist of a php front-end that communicates with a python
back-end over mqtt.

## Development set-up

You need python, paho-mqtt-client and apache+php. 

To install the python dependencies, run 'pip install -r requirements.txt'.

### data

Data is stored in 'data'. In production it is also committed to git, but for
local development it's probably better to use fake data and keep it out of git.
To get started, copy the files from `fakedata`.

### docker-compose

If you don't want to install apache and an mqtt server yourself you can use
docker-compose for local development. Simply running `docker-compose up` will
start an mqtt server on port 1883, an apache+php server serving the files in
'www' on port 4242, and hook
them up to each other. All that's left is to run `kassa.py` and point your
browser at http://localhost:4242
