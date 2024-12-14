import os
import sys
import re
import configparser
from colorama import init, Fore, Back, Style
from datetime import datetime

# Initialize Colorama for cross-platform color support
init(autoreset=True)

class ConfigManager:
    def __init__(self, config_file="default_config.ini"):
        self.config = configparser.ConfigParser()
        self.config_file = config_file
        self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_file):
            self.create_default_config()
        self.config.read(self.config_file)

    def create_default_config(self):
        self.config['DEFAULT'] = {
            'HighlightFullLine': 'False'
        }
        self.config['COLORS'] = {
            'DEBUG': 'GREEN',
            'INFO': 'BLUE',
            'WARNING': 'YELLOW',
            'ERROR': 'MAGENTA',
            'CRITICAL': 'RED'
        }
        try:
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
        except Exception as e:
            print(f"Error creating default config file: {e}")
            sys.exit(1)

    def get(self, section, option):
        try:
            return self.config.get(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            print(f"Config error: {e}")
            sys.exit(1)

    def get_section_items(self, section):
        try:
            return self.config.items(section)
        except configparser.NoSectionError as e:
            print(f"Config section error: {e}")
            sys.exit(1)

class LogViewer:
    def __init__(self, logfile, config):
        self.logfile = logfile
        self.config = config
        self.log_format = re.compile(r"(?P<datetime>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) \[(?P<severity>[A-Z]+)\] (?P<source>[\w:]+) - (?P<message>.+)")
        self.highlight_full_line = self.config.get('DEFAULT', 'HighlightFullLine').lower() == 'true'
        self.colors = dict(self.config.get_section_items('COLORS'))
        self.logs = self.load_logs()
        self.filtered_logs = self.logs.copy()
        self.current_level = 'DEBUG'
        self.levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        self.current_index = 0
        self.search_terms = []  # For highlighting search terms

    def load_logs(self):
        logs = []
        try:
            with open(self.logfile, 'r') as file:
                for line in file:
                    log_entry = self.parse_log_line(line.strip())
                    if log_entry:
                        logs.append(log_entry)
        except FileNotFoundError:
            print(f"Log file '{self.logfile}' not found.")
            sys.exit(1)
        return logs

    def parse_log_line(self, line):
        match = self.log_format.match(line)
        if match:
            return match.groupdict()
        return None

    def filter_logs(self, level):
        level_index = self.levels.index(level)
        self.filtered_logs = [log for log in self.logs if self.levels.index(log['severity']) >= level_index]
        self.current_index = 0

    def apply_search_highlight(self, message):
        reset = Style.RESET_ALL
        for term in self.search_terms:
            message = re.sub(f"({re.escape(term)})", lambda m: f"{Back.YELLOW}{Fore.BLACK}{m.group(1)}{reset}", message, flags=re.IGNORECASE)
        return message

    def highlight_line(self, log):
        severity = log['severity']
        color_mapping = {
            'DEBUG': Fore.GREEN,
            'INFO': Fore.BLUE,
            'WARNING': Fore.YELLOW,
            'ERROR': Fore.MAGENTA,
            'CRITICAL': Fore.RED
        }
        color = color_mapping.get(severity, Fore.WHITE)
        reset = Style.RESET_ALL
        message = self.apply_search_highlight(log['message'])

        if self.highlight_full_line:
            return f"{color}{log['datetime']} [{severity}] {log['source']} - {message}{reset}"
        else:
            highlighted_severity = f"{color}[{severity}]{reset}"
            return f"{log['datetime']} {highlighted_severity} {log['source']} - {message}"

    def display_logs(self):
        print("\n" + "-" * 50)
        for i, log in enumerate(self.filtered_logs):
            prefix = "> " if i == self.current_index else "  "
            print(f"{prefix}{self.highlight_line(log)}")
        print("-" * 50)

    def reset_view(self):
        self.filtered_logs = self.logs.copy()
        self.current_level = 'DEBUG'
        self.current_index = 0
        self.search_terms = []  # Clear search terms

    def navigate_logs(self, direction):
        if direction == 'up' and self.current_index > 0:
            self.current_index -= 1
        elif direction == 'down' and self.current_index < len(self.filtered_logs) - 1:
            self.current_index += 1

    def add_search_term(self, term):
        if term not in self.search_terms:
            self.search_terms.append(term)

    def get_logs_by_range(self, level, count):
        level_index = self.levels.index(level)
        result = []
        for i, log in enumerate(self.logs):
            if self.levels.index(log['severity']) >= level_index:
                start = max(0, i - count)
                result.extend(self.logs[start:i + 1])
        self.filtered_logs = result

class LogCLI:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.logfile = self.get_latest_logfile()
        self.viewer = LogViewer(self.logfile, self.config_manager)
        self.viewer.display_logs()  # Show initial logs

    def get_latest_logfile(self):
        logfiles = [f for f in os.listdir('.') if f.endswith('.log')]
        if not logfiles:
            print("No log files found in the current directory.")
            sys.exit(1)
        return max(logfiles, key=os.path.getmtime)

    def run(self):
        while True:
            command = input("Enter command (+/-/f [keyword]/q/0-4/4-20/r): ").strip()
            if command == '+':
                self.increase_filter_level()
            elif command == '-':
                self.decrease_filter_level()
            elif command.startswith('f '):
                keyword = command[2:]
                self.viewer.add_search_term(keyword)
                self.viewer.display_logs()
            elif command == 'q':
                break
            elif command == 'up':
                self.viewer.navigate_logs('up')
                self.viewer.display_logs()
            elif command == 'down':
                self.viewer.navigate_logs('down')
                self.viewer.display_logs()
            elif command in [str(i) for i in range(5)]:
                self.set_filter_by_number(int(command))
            elif '-' in command:
                self.handle_range_command(command)
            elif command == 'r':
                self.viewer.reset_view()
                self.viewer.display_logs()
            else:
                self.viewer.display_logs()

    def increase_filter_level(self):
        current_index = self.viewer.levels.index(self.viewer.current_level)
        if current_index < len(self.viewer.levels) - 1:
            self.viewer.current_level = self.viewer.levels[current_index + 1]
            self.viewer.filter_logs(self.viewer.current_level)
            self.viewer.display_logs()

    def decrease_filter_level(self):
        current_index = self.viewer.levels.index(self.viewer.current_level)
        if current_index > 0:
            self.viewer.current_level = self.viewer.levels[current_index - 1]
            self.viewer.filter_logs(self.viewer.current_level)
            self.viewer.display_logs()

    def set_filter_by_number(self, number):
        if 0 <= number < len(self.viewer.levels):
            self.viewer.current_level = self.viewer.levels[number]
            self.viewer.filter_logs(self.viewer.current_level)
            self.viewer.display_logs()

    def handle_range_command(self, command):
        try:
            level_str, count_str = command.split('-')
            level = int(level_str)
            count = int(count_str)
            if 0 <= level < len(self.viewer.levels):
                log_level = self.viewer.levels[level]
                self.viewer.get_logs_by_range(log_level, count)
                self.viewer.display_logs()
        except ValueError:
            print("Invalid range format. Use <level>-<count>, e.g., 4-20.")

if __name__ == "__main__":
    cli = LogCLI()
    cli.run()
