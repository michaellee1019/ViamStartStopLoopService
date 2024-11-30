import asyncio
import time

from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions
from viam.components.motor import Motor
from viam.components.board import Board
from viam.components.sensor import Sensor
from viam.components.gantry import Gantry
from viam.components.camera import Camera
from viam.services.mlmodel import MLModelClient
from viam.services.vision import VisionClient

color_to_height = {
    "red": 500,
    "blue": 410,
    "yellow": 420,
    "orange": 420,
}

async def connect():
    opts = RobotClient.Options.with_api_key( 
        api_key='z5n48kydos6eu43iyee8hnk4o7zuhx5w',
        api_key_id='225e16fb-ccf8-41f6-96b7-083d087e8479'
    )
    return await RobotClient.at_address('movingvs-main.f95uzv5arf.viam.cloud', opts)

async def set_pin_for_detection(detections, pin):
    if len(detections) > 0:
        y_min = detections[0].y_min
        y_endstop = color_to_height[detections[0].class_name]
        if y_min <= y_endstop:
            await pin.set(True)
            time.sleep(10.0)
            return True
    await pin.set(False)
    return False

async def main():
    machine = await connect()
    
    # Note that the pin supplied is a placeholder. Please change this to a valid pin you are using.
    # pi
    pi = Board.from_robot(machine, "pi")
    pin_yellow = await pi.gpio_pin_by_name(name="11")
    pin_orange = await pi.gpio_pin_by_name(name="13")
    pin_blue = await pi.gpio_pin_by_name(name="15")
    pin_red = await pi.gpio_pin_by_name(name="16")
    detect_yellow = VisionClient.from_robot(machine, "detect-yellow")
    detect_orange = VisionClient.from_robot(machine, "detect-orange")
    detect_blue = VisionClient.from_robot(machine, "detect-blue")
    detect_red = VisionClient.from_robot(machine, "detect-red")

    orange_detections = await detect_orange.get_detections_from_camera("camera-flipped")
    print(f"orange_detections get_detections return value: {orange_detections}")

    yellow_detections = await detect_yellow.get_detections_from_camera("camera-flipped")
    print(f"yellow_detections get_detections return value: {yellow_detections}")

    blue_detections = await detect_blue.get_detections_from_camera("camera-flipped")
    print(f"blue_detections get_detections return value: {blue_detections}")

    red_detections = await detect_red.get_detections_from_camera("camera-flipped")
    print(f"red_detections get_detections return value: {red_detections}")


    while True:
        orange_detections = await detect_orange.get_detections_from_camera("camera-flipped")
        orange_set = await set_pin_for_detection(orange_detections, pin_orange)
        print("orange was set to", orange_set)

        yellow_detections = await detect_yellow.get_detections_from_camera("camera-flipped")
        yellow_set = await set_pin_for_detection(yellow_detections, pin_yellow)
        print("yellow was set to", yellow_set)

        blue_detections = await detect_blue.get_detections_from_camera("camera-flipped")
        blue_set = await set_pin_for_detection(blue_detections, pin_blue)
        print("blue was set to", blue_set)

        red_detections = await detect_red.get_detections_from_camera("camera-flipped")
        red_set = await set_pin_for_detection(red_detections, pin_red)
        print("red was set to", red_set)

if __name__ == '__main__':
    asyncio.run(main())