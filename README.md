# xonotic-server-status
Gets the status of a Xonotic server and returns a dictionary object.

Nabbed the ping packet data from wireshark and figured out the response manually. :)

Originally created to see if certain maps were in play for the defrag gamemode.

## Usage:

Basic usage from the command line (prints hostname, mapname and players)

```bash
./xsstat.py host [port]
```

Using in python

Available keys are:
'players_data_array', 'gamename', 'modname', 'gameversion', 'sv_maxclients', 'clients', 'bots', 'mapname', 'hostname', 'protocol', 'qcstatus', 'd0_blind_id', 'players'

With the exception of the player object, values are stores as a bytes object.

Printing a player object, will display ping, player name and score. 

Useful properties and methods of a player object:
- player.ping
- player.name
- player.score_or_spec()

```python
import xsstat

info = xsstat.ping("127.0.0.1", 26000)

print(info['hostname'].decode())

print(info['mapname'].decode())

if info['mapname'].decode() == "map_name":
    print("\a")
    print("Its your favourite map, get a better time!")

for player in info['players']:
    print(player)
```

It's nice to combine with watch to keep up to date
```bash
watch -d -n 60 "./xsstat.py host [port]"
```
