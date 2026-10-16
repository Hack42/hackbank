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

### Store the receipt logo in the Epson

Receipts use NV logo 1 already stored in the printer (`FS p 1 3`, the existing
`LOGO` constant). Upload a replacement once with:

```sh
# Stop the kassa backend before uploading.
.venv/bin/python load_printer_logo.py images/hack42.png --write --test-print
```

The script reads `pos.serial` from `config.yaml` (default `/dev/ttyKASSA`,
19200 baud). Use `--config`, `--port`, or `--baudrate` to override it. Without
`--write` it only prepares the image; `--output logo.bin` exports the `FS q`
command for offline inspection. `--test-print` prints the stored logo after
uploading. Restart the backend afterwards.

The default stored width is 192 dots; `LOGO` prints at twice the stored width
and height, so the printed width is at most 384 dots. `--width` changes the
stored width. Images retain their aspect ratio; transparent pixels and padding
become white. Only near-white pixels (all RGB channels at least 245) remain
white; every other color becomes solid black, without dithering.
Stored logos persist after power-off; receipt generation does not
upload the image again.

Epson's [FS q command](https://download4.epson.biz/sec_pubs/pos/reference_en/escpos/fs_lq.html)
replaces **all** existing NV logos/graphics and resets the printer. Run the
script only when changing the logo, with the backend stopped, and keep the
printer powered on until it finishes. A successful serial write cannot confirm
that the printer accepted the logo; verify the test print. The printer must
support the same legacy NV commands already used for the receipt header.

### data

Data is stored in 'data'. In production it is also committed to git, but for
local development it's probably better to use fake data and keep it out of git.
To get started, copy the files from `fakedata`.

### docker-compose

For the self-contained UI development setup at **http://localhost:4123**:

```sh
docker compose -f compose.dev.yaml up -d --build
```

This runs PHP, MQTT, and the unchanged Python backend in project-specific
containers. The UI assets are mounted from `www`, so edits appear on refresh.
Sample members, balances, products, and stock are seeded once in the ignored
`dev/data` directory. This setup does not use production data or hardware;
the door command targets the development broker and no printer is connected.
All CSS, icons, and JavaScript are served locally, with no CDN or web fonts.

Member and user accounts use 84px-tall buttons, 50% taller than the original
compact rows, with page tabs when needed. At 1920×1080 a page holds 42 accounts
(six columns and seven rows); smaller windows calculate their capacity from
the available space. Cash and amount
controls remain above the grid, and the receipt and command bar stay visible.
Filtering keeps the same button sizes, expands results on backspace, and
restores the previous selection and page when cleared. Typing and pasting
both update the filter; Tab still completes a unique match.
Products and commands retain pages of up to 56 buttons (8×7) at 1920×1080,
or 25 buttons on smaller screens. The command bar's Enter button submits the
same command as pressing Enter on the keyboard.
Clicking the Hack42 logo also sends Abort and clears the command input.
The Sounds menu and command search omit Deur off/on, Groove Salad, Jazz Radio
Blues, Kill Music, Louder and Quieter.

Account themes use the existing `account-<username>` CSS classes. `stitch`
has a local Stitch icon, a `#6088B0` background and bold white text; `BugBlue`
has a slowly animated blue glitter background and white text. Balance badges
keep their debt colours, and the glitter respects reduced-motion settings.
See `www/images/users/README.md` for the icon source.

The Music and Home Assistant shortcuts load their requested pages in the
left-hand iframe and include links to open them in a separate tab. Home
Assistant is configured to allow embedding. YouTube's homepage still blocks
embedding, so its toolbar includes a separate-tab hint.
The [supplied Hack42 logo](https://johnkr.com/wp-content/uploads/sites/2/2015/12/Hack42.png)
is already included as `www/images/Hack42.png` and is now displayed in the header.

To stop this setup, run `docker compose -f compose.dev.yaml down`. To reset
the sample data, stop the containers, remove `dev/data`, and start them again.

The original development setup remains available:

If you don't want to install apache and an mqtt server yourself you can use
docker-compose for local development. Simply running `docker-compose up` will
start an mqtt server on port 1883, an apache+php server serving the files in
'www' on port 4242, and hook
them up to each other. All that's left is to run `kassa.py` and point your
browser at http://localhost:4242
