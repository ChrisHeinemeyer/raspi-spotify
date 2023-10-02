from __future__ import annotations

import datetime
import logging
import socket
import subprocess
import sys
from enum import Enum, Flag, auto

from dateutil.parser import parser

import pisugar

HOST = "127.0.0.1"
PORT = 8423


class PisugarCommands(Enum):
    GET_BATTERY = "get battery"  # battery level %
    GET_RTC_TIME = "get rtc_time"  # rtc clock

    RTC_WEB = "rtc_web"  # sync time web => rtc & pi
    RTC_PI2RTC = "rtc_pi2rtc"  # sync time pi => rtc
    RTC_RTC2PI = "rtc_rtc2pi"  # sync time rtc => pi

    RTC_ALARM_SET = "rtc_alarm_set"  # set rtc wakeup alarm
    GET_RTC_ALARM_TIME = "get rtc_alarm_time"
    GET_RTC_ALARM_ENABLED = "get rtc_alarm_enabled"


class Weekdays(Flag):
    SUNDAY = auto()
    MONDAY = auto()
    TUESDAY = auto()
    WEDNESDAY = auto()
    THURSDAY = auto()
    FRIDAY = auto()
    SATURDAY = auto()

    def day_str(self):
        return [d.name for d in Weekdays if d in self]


WEEKENDS: Weekdays = Weekdays.SUNDAY | Weekdays.SATURDAY
WEEKDAYS = (
    Weekdays.MONDAY
    | Weekdays.TUESDAY
    | Weekdays.WEDNESDAY
    | Weekdays.THURSDAY
    | Weekdays.FRIDAY
)
ALL_DAYS = WEEKENDS | WEEKDAYS


class Pisugar:
    def __init__(self, host: str = HOST, port: int = PORT):
        self.logger = logging.getLogger(__file__)
        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger.debug(f"Connecting to pisugar socket at {host}: {port})")
        self.sock.connect((host, port))

    def shut_down(self, countdown_s: int = 90, num_retries: int = 10):
        args = [
            "pisugar-poweroff",
            "--model",
            "PiSugar 3",
            "--countdown",
            str(countdown_s),
            "--retries",
            str(num_retries),
        ]

        self.logger.debug(f"Restarting with args {args}")
        subprocess.run(args)

    def send_command(self, cmd: PisugarCommands, *args):
        args = [cmd.value] + list(args)
        send_str = " ".join([str(a) for a in args])

        self.logger.debug(f"Sending {send_str.encode()}")
        self.sock.send(send_str.encode())
        res = self.sock.recv(1024)
        self.logger.debug(f"Received {res}")
        return self.parse_response(res.decode())

    def parse_response(self, response: str):
        return response[response.find(":") + 1 :].strip()

    def set_alarm_time(self, alarm_time: datetime.datetime, days: Weekdays = ALL_DAYS):
        self.logger.debug(
            f"Setting alarm for {alarm_time.isoformat()} for days {days.day_str()}"
        )
        self.send_command(
            PisugarCommands.RTC_ALARM_SET, alarm_time.isoformat(), days.value
        )

        received_time = self.send_command(PisugarCommands.GET_RTC_ALARM_TIME)
        self.logger.debug(f"Received alarm time {received_time}")

    def set_alarm_time_from_now(self, **kwargs):
        self.logger.debug(f"Setting alarm with kwargs {kwargs}")
        self.send_command(PisugarCommands.RTC_WEB)
        time_now = parser().parse(self.send_command(PisugarCommands.GET_RTC_TIME))
        self.logger.debug(f"Current time is {time_now}")
        dt = datetime.timedelta(**kwargs)
        alarm_time = time_now + dt
        self.logger.debug(f"Alarm time is {alarm_time}")
        self.set_alarm_time(alarm_time)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s: %(message)s",
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    ps = Pisugar()

    ps.send_command(PisugarCommands.RTC_WEB)
    ps.send_command(PisugarCommands.RTC_ALARM_SET, "2023-09-29T20:20:30.000-07:00", 127)
    ps.send_command(PisugarCommands.GET_RTC_ALARM_TIME)
    ps.send_command(PisugarCommands.GET_RTC_ALARM_ENABLED)
    ps.set_alarm_time_from_now(minutes=5)
    ps.shut_down()
