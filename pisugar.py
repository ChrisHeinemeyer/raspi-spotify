import socket
import subprocess
from enum import Enum

HOST = "127.0.0.1"
PORT = 8423


class PisugarCommands(Enum):
    GET_BATTERY = "get battery"
    GET_RTC_TIME = "get rtc_time"


class Pisugar:
    def __init__(self, host: str = HOST, port: int = PORT):
        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
        send_str = f"{cmd.name}"
        self.sock.send(send_str.encode())
        res = self.sock.recv(1024)
        return res.decode()


if __name__ == "__main__":
    ps = Pisugar()
    for command in PisugarCommands:
        print(command)
        res = ps.get_command(command)
        print(res)
