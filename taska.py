import csv
from datetime import datetime
import re
import numpy as np


def parse_log_file(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()

    header_line = lines[0].strip()
    header_parts = header_line.split()
    timestamp_format = "%m/%d/%y %I:%M:%S %p"
    header_timestamp = datetime.strptime(" ".join(header_parts[4:]), timestamp_format)

    id_mapping = {}
    i = 1
    pattern = r"Value (.*) \((.*)\): (\d+)"
    parameters = [
        "ams.pack.voltage",
        "ams.pack.current",
        "pcm.wheelSpeeds.frontLeft",
        "pcm.wheelSpeeds.frontRight",
        "pcm.wheelSpeeds.backLeft",
        "pcm.wheelSpeeds.backRight",
    ]

    while i < len(lines) and lines[i].startswith('Value'):
        match = re.search(pattern, lines[i])
        if match:
            value = match.group(1).strip()
            descriptor = match.group(2).strip()
            id_ = match.group(3).strip()
            if descriptor in parameters:
                id_mapping[id_] = descriptor
        else:
            print(f"Warning: Line {lines[i]} does not match the expected format.")
        i += 1

    data = {param: {} for param in parameters}

    while i < len(lines):
        line = lines[i].strip()
        if line:
            parts = line.split(',')
            timestamp_ms = int(parts[0].strip())
            id_ = str(parts[1].strip())
            value = float(parts[2].strip())

            description = id_mapping.get(id_)
            if description:
                data[description][timestamp_ms] = value
        i += 1

    return data, header_timestamp


def build_table(data, timestamps):
    sorted_timestamps = sorted(timestamps)

    table = []
    for ts in sorted_timestamps:
        row = {"Timestamp": ts}
        for param in data.keys():
            row[param] = data[param].get(ts, "")
        table.append(row)

    write_results(table, 'task_a_data.txt')
    return table


def write_results(table, output_file):
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = table[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in table:
            writer.writerow(row)

    print(f"Table written to {output_file}")


def calculate_speed_statistics(table):
    speeds = []

    for row in table:
        for param in ["pcm.wheelSpeeds.frontLeft", "pcm.wheelSpeeds.frontRight", "pcm.wheelSpeeds.backLeft",
                      "pcm.wheelSpeeds.backRight"]:
            if row[param] != "":
                speeds.append(row[param])

    speeds = np.array(speeds)
    min_speed = np.min(speeds)
    max_speed = np.max(speeds)
    avg_speed = np.mean(speeds)

    return min_speed, max_speed, avg_speed


def calculate_energy(table):
    power_consumption = []
    time_diffs = []

    last_timestamp = None

    for row in table:
        ts = row["Timestamp"]
        if row["ams.pack.voltage"] != "" and row["ams.pack.current"] != "":
            voltage = row["ams.pack.voltage"]
            current = row["ams.pack.current"]
            power = voltage * current / 1000.0
            power_consumption.append((ts, power))

            if last_timestamp is not None:
                time_diff = (ts - last_timestamp) / 1000.0
                time_diffs.append(time_diff)

            last_timestamp = ts

    power_values = np.array([power for _, power in power_consumption])
    time_diffs = np.array(time_diffs)

    return np.sum(power_values[:-1] * time_diffs) / 3600


if __name__ == "__main__":
    data, header_timestamp = parse_log_file('TaskA.csv')

    all_timestamps = set()
    for param_data in data.values():
        all_timestamps.update(param_data.keys())

    table = build_table(data, all_timestamps)

    min_speed, max_speed, avg_speed = calculate_speed_statistics(table)
    print(f"Minimum Speed: {min_speed:.2f} MPH")
    print(f"Maximum Speed: {max_speed:.2f} MPH")
    print(f"Average Speed: {avg_speed:.2f} MPH")

    energy_consumed = calculate_energy(table)
    print(f"Total Energy Consumed: {energy_consumed:.2f} kWh")
