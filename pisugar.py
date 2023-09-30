import logging
import socket
import subprocess
import sys
from enum import Enum

HOST = "127.0.0.1"
PORT = 8423


class PisugarCommands(Enum):
    GET_BATTERY = "get battery"
    GET_RTC_TIME = "get rtc_time"


class Pisugar:
    def __init__(self, host: str = HOST, port: int = PORT):
        self.logger = logging.getLogger(__file__)
        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger.debug(f"Connecting to pisugar socket at {host}: {port})")
        self.sock.connect((host, port))

    def restart(countdown_s: int = 10, num_retries: int = 10):
        subprocess.run(
            [
                "pisugar-poweroff",
                "--model",
                "PiSugar 3",
                "--countdown",
                str(countdown_s),
                "--retries",
                str(num_retries),
            ]
        )

    def get_command(self, cmd: PisugarCommands, *args):
        send_str = f"{cmd.value}"
        self.logger.debug(f"Sending {send_str.encode()}")
        self.sock.send(send_str.encode())
        res = self.sock.recv(1024)
        self.logger.debug(f"Received {res}")
        return res.decode()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s: %(message)s",
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    ps = Pisugar()
    for command in PisugarCommands:
        res = ps.get_command(command)
