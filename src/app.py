import os
import comtypes
from pycaw.pycaw import AudioUtilities
from pycaw.utils import AudioDevice  # Import AudioDevice for type hinting
from pycaw.api.endpointvolume import IAudioEndpointVolume
from comtypes import COMError  # Import COMError to handle exceptions
import time
import json


def find_target_devices(target_devices_map: dict[str, float]) -> list[AudioDevice]:
    """
    Find target devices based on their friendly names.
    """
    devices: list[AudioDevice] = AudioUtilities.GetAllDevices()
    target_devices: list[AudioDevice] = []
    for device in devices:
        try:
            # Ensure the device has a FriendlyName before checking it
            if device.FriendlyName:
                # Adjust the input level here
                print(f"ID: {device.id}, name: {device.FriendlyName}")
                if device.FriendlyName in target_devices_map:
                    device._last_volume = -0.1  # Initialize last volume to 0.0
                    target_devices.append(device)

        except COMError as e:
            # Log the error and skip the problematic device
            print(f"Error accessing device properties: {e}")
        except Exception as e:
            # Log any other unexpected errors
            print(f"Unexpected error: {e}")
    return target_devices


def get_device_input_volume(device: AudioDevice) -> float | None:
    """
    Get the input volume for a given device.
    """
    try:
        endpoint_volume = device._dev.Activate(
            IAudioEndpointVolume._iid_, comtypes.CLSCTX_ALL, None
        ).QueryInterface(IAudioEndpointVolume)

        # Get the master volume level (0.0 to 1.0)
        current_volume = endpoint_volume.GetMasterVolumeLevelScalar()
        return current_volume
    except Exception as e:
        print(f"Failed to get volume for {device.FriendlyName}: {e}")
        return None  # Return None if there's an error


def set_device_input_volume(device: AudioDevice, input_level: float):
    """
    Set the input volume for a given device.
    """
    try:
        endpoint_volume = device._dev.Activate(
            IAudioEndpointVolume._iid_, comtypes.CLSCTX_ALL, None
        ).QueryInterface(IAudioEndpointVolume)

        # Set the master volume level (0.0 to 1.0)
        endpoint_volume.SetMasterVolumeLevelScalar(input_level, None)
        print(f"Set volume for {device.FriendlyName}")
    except Exception as e:
        print(f"Failed to set volume for {device.FriendlyName}: {e}")


def set_target_devices_input_volume(
    target_devices: list[AudioDevice]
):
    """
    Set the input volume for the target devices.
    """
    exit_prompt = "...press ^C to exit"
    target_devices_map, _ = get_config()
    for device in target_devices:
        # Get the target volume for the device
        target_volume = target_devices_map.get(device.FriendlyName, 1.0)
        # Set the input volume for the device
        current_volume = get_device_input_volume(device)
        if current_volume is not None:
            # Check if the current volume is different from the target volume
            if not abs(current_volume - target_volume) < 0.001:  # Allow small tolerance
                print(
                    f"Current: {current_volume}, setting {device.FriendlyName} to {target_volume}, {exit_prompt}"
                )
                set_device_input_volume(device, target_volume)
            else:
                if (
                    device._last_volume is not None
                    and not abs(device._last_volume - current_volume) < 0.001
                ):
                    print(
                        f"Volume for {device.FriendlyName} is already at {target_volume}, {exit_prompt}"
                    )
            device._last_volume = current_volume  # Store the last volume for the device
        else:
            print(
                f"Could not get current volume for {device.FriendlyName}, {exit_prompt}"
            )


def maintain_target_devices_input_volume(
    target_devices: list[AudioDevice],
    interval: float,
):
    """
    Maintain the input volume for the target devices.
    """
    # launch an infinite loop to maintain target devices' input volume for every 100ms
    while True:
        try:
            # Set the input volume for the target devices
            set_target_devices_input_volume(target_devices)

        except KeyboardInterrupt:
            print("Exiting...")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
        time.sleep(interval)  # Wait for 100 milliseconds

def find_config() -> str:
    """
    Find the config.json file in the current or parent directory.
    """
    for path in ("./resource/config.json", "../resource/config.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                print(f"Found config file at: {path}")
                return path
        except FileNotFoundError:
            continue
    raise FileNotFoundError("config.json not found in ./resource/ or ../resource/")

def get_config() -> tuple[dict[str, float], float] | None:
    """
    Get the target devices name and volume from config.json
    """
    path = os.environ.get("CONFIG_PATH", "./resource/config.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
            target_devices_map = config["target_devices_map"]
            interval = config["interval"]
            return target_devices_map, interval
    except FileNotFoundError as e:
        print(
            f"{path} not found, please create an {path} file"
        )
    except Exception as e:
        print(f"Error reading config.json: {e}")
        raise e


def main():
    # read target device names and volumes from config.json
    config_path = find_config()
    os.environ["CONFIG_PATH"] = config_path
    target_devices_map, interval = get_config()
    # Print the target device names and volumes
    print("Target device names and volumes from config:")
    for name, volume in target_devices_map.items():
        print(f"    {name}: {volume}")

    # Find the target devices based on their friendly names
    target_devices = find_target_devices(target_devices_map)

    print("Target devices found:")
    for device in target_devices:
        print(f"    {device.FriendlyName}")

    maintain_target_devices_input_volume(target_devices, interval)


if __name__ == "__main__":
    main()
