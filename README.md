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

This runs PHP, MQTT, the unchanged Python backend, and a demo audio controller
in project-specific containers. The UI assets are mounted from `www`, so edits appear on refresh.
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
The larger Members/Other users buttons and page tabs support touch selection.
Commands are grouped into Products, Users, Sales, Wholesale, Market and Misc,
with an Abort action and a Settings section. Category tabs provide larger
controls for each section. Manage members contains member administration;
all underlying commands remain available. Remove item edits the current
unbilled sale; transaction undo is a separate action. Door open retains the
existing configured door command.

Settings offers Party, Dark, Banana and Dank Hit modes. Party mode reflects
backend state and can be disabled even while another question is pending.
A missing printer no longer prevents exit: settlement totals and their history
are saved in the party state before attempting to print. No sale or account
balance is cleared by changing this setting.

Appearance settings apply to this browser and survive reloads. The command bar
also accepts `darkmodeon` / `darkmodeoff`, `bananamodeon` / `bananamodeoff`, and
`dankmodeon` / `dankmodeoff`. The banana appears at a random screen location,
lets clicks through, fades during its final two seconds, and disappears within
one hour of activation; refreshing does not extend that deadline. Dank Hit mode
plays the supplied hitmarker sample through the POS browser audio and displays
a click-through marker for 300ms at each click or tap.

Member and Other users lists have alphabetical Archive tabs for accounts whose
last purchase is older than a year. New accounts with no purchase record use
their last account update as a conservative fallback. A read-only index of
the existing checkout log is shared between sessions, reuses unchanged results,
and reads only appended data after the first scan. Initial reads are capped
at 8MiB. If that window cannot establish a full year's coverage, archives stay
unavailable and accounts remain in the normal lists. Deposits, transfers,
refunds and undo lines are excluded from purchase history.

Clicking a user with an empty sale shows the balance and up to ten recent
purchase line items. Add again uses the current product price and only adds
to the sale, leaving the normal account selection and checkout flow intact.
Reordering is offered only when a historical description identifies one
current product. Older or ambiguous products remain visible as history.
Undo latest transaction appears only for an eligible latest transaction;
the backend rechecks its ID and owner before using the existing undo flow.
The local seed adds stitch, BugBlue, Jos, nino and Anus, two archive examples,
and sample purchase history without resetting existing development balances.
Clicking anywhere in the Hack42 logo, title, and subtitle area sends Abort and
clears the command input.
The Sounds menu and command search omit Deur off/on, Groove Salad, Jazz Radio
Blues, Kill Music, Louder, Quieter and Kassa off/on. The Sounds page also omits
Abort and Christmas; the header reset remains available. Ding Dong, Vergaderen,
Vergaderen Extreme and Throw remain on that page after playback. Typed sound
commands keep their existing behavior. Sounds provides two large
volume sliders for HackBank POS effects and Space audio. Each reads the current
output volume, applies changes, and refreshes every two seconds while open.
Opening Sounds is silent. Releasing a slider plays a short preview beep on
that output after saving its volume; dragging and automatic refreshes are
silent. At zero volume the output remains muted and no preview plays.
The development audio controller uses in-memory demo levels and never connects
to a sound device; it also simulates preview requests.

Account themes use the existing `account-<username>` CSS classes. `stitch`
has a local Stitch icon, a `#6088B0` background and bold white text; `BugBlue`
has a slowly animated blue glitter background and white text. Jos has a gold
key icon and dark theme; nino has a Ukrainian flag background; the existing Anus
account has an animated plasma effect. These three names match without regard
to case. Balance badges keep their debt colours, and animations respect
reduced-motion settings.
See `www/images/users/README.md` for the icon source.

The Home Assistant shortcut opens its page in the left-hand iframe, with a link
to open it in a separate tab. Music is hidden until a LAN music interface is
available.
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

### Production audio controls

`audio_control.py` uses the system's existing `pactl` command to read and adjust
only `hackbank_pos` (POS effects) and `snapcast` (Space audio). Previews use
the existing `paplay` command and the local `KDE_Beep_ClassicBeep.wav` file,
explicitly selecting the adjusted output at full stream gain so its sink
volume determines the preview level. It does not change
the existing audio routing. `www/audio.php` connects to the controller through
`/run/hackbank-audio/control.sock`; the controller does not open a network port.
Volumes range from 0 to 100 percent; zero also mutes, and a nonzero setting
unmutes that output. Missing devices or an unavailable controller disable the
affected sliders. Financial commands continue through the existing backend.

The supplied systemd unit targets the bar installation at `/home/barapp/kassa`,
runs as kiosk user `bar`, and gives Apache's `www` group access to the socket.
After deploying the UI branch, register and start it as root:

```sh
systemctl enable --now /home/barapp/kassa/deploy/hackbank-audio-control.service
systemctl status hackbank-audio-control.service
```

The unit depends on the existing kiosk PulseAudio/PipeWire socket and named
outputs. The page title remains `Hack42 - HackBank`, the identifier used by the
existing POS audio router. Restart `hackbank-audio-control.service` after
updating its Python controller. Changes to `plugins/sounds.py`, including the
silent Sounds navigation, also require restarting the existing POS backend.
For a different installation, adapt the unit's application path, kiosk user,
web-server group, and runtime audio socket before enabling it.
