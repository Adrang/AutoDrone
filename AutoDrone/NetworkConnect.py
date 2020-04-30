"""
@title
@description
"""
import argparse
import subprocess
import sys

import Andrutil
from Andrutil import TERMINAL_COLUMNS

import AutoDrone


def decode_console(out_raw):
    try:
        out_decoded = out_raw.decode(sys.stdout.encoding)
    except UnicodeDecodeError:
        out_decoded = out_raw.decode('iso-8859-2')
    return out_decoded


def clean_results(command_output):
    results_decoded = decode_console(command_output)
    results_split = [
        each_line.strip()
        for each_line in results_decoded.split('\r\n')
        if len(each_line) > 0
    ]
    return results_split


def netsh_find_ssid_list(mode: str = None):
    command = 'netsh wlan show network'
    if mode:
        command = f'{command} mode={mode}'
    results = subprocess.check_output(command)
    cleaned_results = clean_results(results)

    ssid_list = []
    for each_line in cleaned_results:
        if ':' in each_line:
            line_parts = [
                each_part.strip()
                for each_part in each_line.split(':')
            ]
            line_type = line_parts[0]
            line_name = line_parts[1]
            if line_type.startswith('SSID'):
                ssid_list.append(line_name)
        else:
            pass
    return ssid_list


def netsh_find_interface_list(mode: str = None):
    command = 'netsh wlan show network'
    if mode:
        command = f'{command} mode={mode}'
    results = subprocess.check_output(command)
    cleaned_results = clean_results(results)

    interface_list = []
    for each_line in cleaned_results:
        if ':' in each_line:
            line_parts = [
                each_part.strip()
                for each_part in each_line.split(':')
            ]
            line_type = line_parts[0]
            line_name = line_parts[1]
            if line_type.startswith('Interface name'):
                interface_list.append(line_name)
        else:
            pass
    return interface_list


def netsh_show_interfaces(mode: str = None):
    command = 'netsh wlan show interface'
    if mode:
        command = f'{command} mode={mode}'
    results = subprocess.check_output(command)
    cleaned_results = clean_results(results)

    result_dict = {}
    for each_line in cleaned_results:
        if ':' in each_line:
            line_parts = [
                each_part.strip()
                for each_part in each_line.split(':')
            ]
            line_type = line_parts[0]
            line_name = line_parts[1]
            if len(line_name) > 0:
                result_dict[line_type] = line_name
        else:
            pass
    return result_dict


def netsh_connect_network(network_name: str, interface: str):
    command = f'netsh wlan connect name="{network_name}" interface="{interface}"'
    results = subprocess.check_output(command)
    cleaned_results = clean_results(results)
    connection_success = set(cleaned_results).intersection({'Connection request was completed successfully.'})
    return cleaned_results, connection_success


def netsh_disable_wifi_adapter(adapter_name: str):
    command = f'netsh interface set interface name="{adapter_name}" admin=disabled'
    results = subprocess.check_output(command)
    cleaned_results = clean_results(results)
    return cleaned_results


def netsh_enable_wifi_adapter(adapter_name):
    command = f'netsh interface set interface name="{adapter_name}" admin=enable'
    results = subprocess.check_output(command)
    cleaned_results = clean_results(results)
    return cleaned_results


def netsh_toggle_adapter(adapter_name: str):
    netsh_disable_wifi_adapter(adapter_name=adapter_name)
    netsh_enable_wifi_adapter(adapter_name=adapter_name)
    return


def main(main_args):
    ssid_list = netsh_find_ssid_list()
    interface_results = netsh_show_interfaces()

    print('-' * TERMINAL_COLUMNS)
    for each_ssid in ssid_list:
        print(each_ssid)

    print('-' * TERMINAL_COLUMNS)
    for results_key, results_val in interface_results.items():
        print(results_key)

    print('-' * TERMINAL_COLUMNS)
    print(Andrutil.DATA_DIR)
    print(AutoDrone.DATA_DIR)

    # tello_base_ssid = 'TELLO-'
    # network_found = False
    # scan_count = 0
    # scan_delay = 1
    # while not network_found:
    #     try:
    #         results = subprocess.check_output([
    #             "netsh", "interface", "set", "interface", f"name=Wi-Fi", 'admin=disabled'
    #         ])
    #         print(results)
    #         results = subprocess.check_output([
    #             "netsh", "interface", "set", "interface", f"name=Wi-Fi", 'admin=enabled'
    #         ])
    #         print(results)
    #     except Exception as e:
    #         print(f'{e}')
    #     sleep(scan_delay)
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')

    args = parser.parse_args()
    main(vars(args))


def main(main_args):
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')

    args = parser.parse_args()
    main(vars(args))
