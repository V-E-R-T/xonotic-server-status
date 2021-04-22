#!/usr/bin/env python3

import re
import signal
import socket
import sys
import math
import unicodedata

TIMEOUT = 6
GET_STATUS = bytes.fromhex("ffffffff676574737461747573")
CENTISECOND_DIGITS = 2
SECONDS_IN_A_MINUTE = 60
SECONDS_IN_AN_HOUR = 3600
MINUTES_IN_A_HOUR = 60


class Player:
    'A player object, easier to work with'

    def __init__(self, raw_score, ping, raw_name):
        self.raw_score = raw_score
        self.score = int(float(raw_score))
        self.ping = ping
        self.raw_name = raw_name
        self.name = self.get_name()

    def __str__(self):
        return self.columned_ping_name_score()

    def is_spectating(self):
        if self.score == -666:
            return True
        else:
            return False

    def has_zero_score(self):
        if self.score == 0:
            return True
        else:
            return False

    def score_or_spec(self):
        if self.is_spectating():
            return "Spectator"
        else:
            return self.score

    def time_or_spec(self):
        if self.is_spectating():
            return "Spectator"
        elif self.has_zero_score():
            return "Running"
        else:
            return get_time_from_score(self.score)

    def get_name(self):
        return parse_escape_chars_and_remove_color_codes(self.raw_name)

    def columned_ping_name_score(self):
        off = count_wide_chars(self.get_name())
        return (f"{self.ping:>3} {self.get_name()[:32]:<{32 - off}} "
                f"{self.score_or_spec():>10}")

    def columned_ping_name_time(self):
        off = count_wide_chars(self.get_name())
        return (f"{self.ping:>3} {self.get_name()[:32]:<{32 - off}} "
                f"{self.time_or_spec():>10}")


def count_wide_chars(string):
    count = 0
    for char in string:
        if unicodedata.east_asian_width(char) == 'W':
            count += 1
    return count


def get_time_from_score(score):
    t = score_to_time_dict(score)
    if t['hours'] > 0:
        return f"{t['hours']}:{t['mins']:0>2}:{t['secs']:0>2}.{t['cs']:0>2}"
    else:
        return f"{t['mins']}:{t['secs']:0>2}.{t['cs']:0>2}"


def score_to_time_dict(score):
    total_seconds = int(str(score)[:-CENTISECOND_DIGITS])
    return {'hours': total_hours_from_seconds(total_seconds),
            'mins': minutes_from_seconds(total_seconds),
            'secs': seconds_from_seconds(total_seconds),
            'cs': int(str(score)[-CENTISECOND_DIGITS:])}


def parse_escape_chars_and_remove_color_codes(string):
    return re.sub(r"\^(\^)|\^\d|\^x[0-9a-fA-F]{3}", r"\1", string)


def total_hours_from_seconds(seconds):
    global SECONDS_IN_AN_HOUR
    return math.floor(seconds / SECONDS_IN_AN_HOUR)


def total_minutes_from_seconds(seconds):
    global SECONDS_IN_A_MINUTE
    return math.floor(seconds / SECONDS_IN_A_MINUTE)


def seconds_from_seconds(seconds):
    global SECONDS_IN_A_MINUTE
    return seconds % SECONDS_IN_A_MINUTE


def minutes_from_seconds(seconds):
    return (
        total_minutes_from_seconds(seconds) -
        (MINUTES_IN_A_HOUR * total_hours_from_seconds(seconds))
    )


def parse_status_response(data):
    data_parts = data.rsplit("\n".encode())
    info = parse_server_info_data(data_parts[1])
    info['status_response'] = data_parts[0]
    info['players'] = parse_players_data(data_parts[2:-1])
    info.update(parse_qcstatus_data(info['qcstatus']))
    return info


def parse_server_info_data(svr_data):
    key_value_data_pairs = svr_data.rsplit("\\".encode())
    svr_info = {}
    for i in range(2, len(key_value_data_pairs), 2):
        svr_info[key_value_data_pairs[i-1].decode("utf-8", "ignore")] = \
            key_value_data_pairs[i]
    return svr_info


def parse_players_data(players_data):
    players = []
    for player_data in players_data:
        player_data_array = player_data.rsplit(" ".encode())
        raw_name = player_data.rsplit('"'.encode())[1]
        player = Player(player_data_array[0].decode(),
                        int(player_data_array[1]), raw_name.decode())
        players.append(player)
    return players


def parse_qcstatus_data(qcstatus_data):
    status_parts = qcstatus_data.split(":".encode())
    return {'gametype': status_parts[0].decode(),
            'serverversion': status_parts[1].decode(),
            'mod': status_parts[5].decode()[1:]}


def timeout_handler(signum, frame):
    raise TimeoutError(
        f"Timed out after waiting {TIMEOUT} seconds for a response"
    )


def ping(host="127.0.0.1", uport=26000):
    try:
        port = int(uport)

        if port <= 0 or port > 65535:
            raise ValueError

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(GET_STATUS, (host, port))

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(TIMEOUT)

        while True:
            data, addr = s.recvfrom(1024)

            if addr[0] == host:
                return parse_status_response(data)

    except ValueError:
        print("Port must be an integer value in range 0-65535")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def display(info):
    print(info['hostname'].decode())
    print(info['mapname'].decode())

    if info['gametype'] == "cts":
        for player in sorted(info['players'], key=lambda p: p.score):
            print(player.columned_ping_name_time())
    else:
        for player in sorted(info['players'], key=lambda p: p.score,
                             reverse=True):
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
