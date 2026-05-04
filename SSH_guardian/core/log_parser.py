
from datetime import datetime
from email.generator import Generator
import time


def tail_file(filepath: str) -> Generator[str, None, None]:
        # Open the target file in read-only mode 
        with open(filepath, 'r') as f:
            # Move the file pointer to the end of the file to start reading new lines
            f.seek(0, 2)  # Move to the end of the file

            # Continuously read new lines as they are added to the file
            while True:
                # Read a new line from the file
                line = f.readline()
                # If no new line is found, wait briefly before trying again
                if not line:
                    time.sleep(0.1)  # Sleep briefly to avoid busy waiting
                    continue
                yield line.strip()

def is_ssh_event(line: str) -> bool:
        return 'sshd' in line and ('Failed password' in line or 'Accepted password' in line)

def parse_line(line: str) -> dict | None:
        if not is_ssh_event(line):
            return None
        
        event = {
            'timestamp': extract_timestamp(line),
            'ip': extract_ip(line),
            'username': extract_username(line),
            'type': get_event_type(line)
        }
        return event

def extract_ip(line: str) -> str | None:
    # Extract IP address from log line
    return None


def extract_username(line: str) -> str | None:
    # Extract username from log line
    return None


def extract_timestamp(line: str) -> datetime | None:
    # Extract timestamp from log line
    return None


def get_event_type(line: str) -> str | None:
    if 'Failed password' in line:
        return 'failed'
    elif 'Accepted password' in line:
        return 'successful'
    return None