# hackbank

The hackbank consist of a php front-end that communicates with a python
back-end over mqtt.

## Development set-up

You need python, paho-mqtt-client and apache+php. 

To install the python dependencies, run 'pip install -r requirements.txt'.

### Printer and cash drawer

The POS serial port defaults to `/dev/ttyKASSA`. Install the udev rule on the
machine connected to the Prolific PL2303 USB serial adapter:

```sh
sudo install -m 0644 udev/99-kassa.rules /etc/udev/rules.d/99-kassa.rules
sudo udevadm control --reload-rules
sudo udevadm trigger --action=add --subsystem-match=tty
sudo udevadm settle
ls -l /dev/ttyKASSA
```

Give the backend user membership of `dialout` and restart the backend. Set
`pos.serial.port: /dev/ttyKASSA` in an existing `config.yaml`; local overrides
remain supported. The adapter has no unique serial number, so this rule assumes
only one `067b:2303` adapter is connected. With several identical adapters, narrow
the rule to the appropriate USB port before installing it.

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
