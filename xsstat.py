#!/usr/bin/env python3

import re, signal, socket, sys, math

TIMEOUT = 6
XONOPINGBIN = bytes.fromhex("ffffffff676574737461747573")


class Player:
    'A player object, easier to work with'

    def __init__(self, score, ping, raw_name):
        self.score = score
        self.ping = ping
        self.raw_name = raw_name
        self.name = self.get_name()

    def __str__(self):
        return (
            f"{self.ping:>3} {self.get_name()[:32]:32} {self.time_or_spec():>10}"
        )

    def is_spectating(self):
        if self.score == -666:
            return True
        return False

    def score_or_spec(self):
        if self.is_spectating():
            return "Spectator"
        return self.score

    def time_or_spec(self):
        if self.is_spectating():
            return "Spectator"
        elif self.score == 0:
            return "Running"
        elif len(str(self.score)) <= 2:
            return f"0:00.{self.score:0>2}"
        else:
            score_seconds = int(str(self.score)[:-2])
            hours = total_hours_from_seconds(score_seconds)
            mins = minutes_from_seconds(score_seconds)
            secs = seconds_from_seconds(score_seconds)
            ms = int(str(self.score)[-2:])

            if hours > 0:
                return f"{hours}:{mins:0>2}:{secs:0>2}.{ms:0>2}"
            else:
                return f"{mins}:{secs:0>2}.{ms:0>2}"

    def get_name(self):
        unicode_name = self.raw_name.decode("utf-8", "ignore")

        color_code = r"\^x[0-9a-fA-F]{3}"
        cd_code = r"\^\d"

        no_color_codes = re.sub(color_code, "", unicode_name)
        no_codes = re.sub(cd_code, "", no_color_codes)

        return no_codes


def total_hours_from_seconds(seconds):
    return math.floor(seconds / 3600)


def total_minutes_from_seconds(seconds):
    return math.floor(seconds / 60)


def seconds_from_seconds(seconds):
    return seconds % 60


def minutes_from_seconds(seconds):
    return (
        total_minutes_from_seconds(seconds) -
        (60 * total_hours_from_seconds(seconds))
    )


def dp_protocol_parse(data):

    players = []
    data_parts = data.rsplit("\n".encode())

    info = {
        'status_response': data_parts[0],
        'players_data_array': data_parts[2:-1]
    }

    server_info_data = data_parts[1]
    key_value_data_pairs = server_info_data.rsplit("\\".encode())

    for i in range(2, len(key_value_data_pairs), 2):
        info[key_value_data_pairs[i-1].decode("utf-8", "ignore")] = \
            key_value_data_pairs[i]

    for player_data in info['players_data_array']:
        player_data_array = player_data.rsplit(" ".encode())
        raw_name = player_data.rsplit('"'.encode())[1]

        player = Player(
                int(player_data_array[0]), int(player_data_array[1]),
                raw_name)

        players.append(player)

    info['players'] = players

    return info


def handler(signum, frame):
    raise TimeoutError(
        f"Timed out after waiting {TIMEOUT} seconds for a response"
    )


def ping(host="127.0.0.1", uport=26000):
    try:
        port = int(uport)

        if port <= 0 or port > 65535:
            raise ValueError

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(XONOPINGBIN, (host, port))

        signal.signal(signal.SIGALRM, handler)
        signal.alarm(TIMEOUT)

        while True:
            data, addr = s.recvfrom(1024)

            if addr[0] == host:
                return dp_protocol_parse(data)

    except ValueError:
        print("Port must be an integer value in range 0-65535")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def display(info):
    
    print(info['hostname'].decode())
    print(info['mapname'].decode())

    for player in info['players']:
        print(player)


def __main__():
    host = "127.0.0.1"
    port = 26000

    if len(sys.argv) > 1:
        host = sys.argv[1]

    if len(sys.argv) > 2:
        port = sys.argv[2]
            
    display(ping(host, port))


if __name__ == "__main__":
            __main__()
