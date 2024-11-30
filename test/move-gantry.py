import asyncio

from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions
from viam.components.motor import Motor
from viam.components.gantry import Gantry
from viam.components.board import Board
from viam.components.sensor import Sensor

async def connect():
    opts = RobotClient.Options.with_api_key( 
        api_key='z5n48kydos6eu43iyee8hnk4o7zuhx5w',
        api_key_id='225e16fb-ccf8-41f6-96b7-083d087e8479'
    )
    return await RobotClient.at_address('movingvs-main.f95uzv5arf.viam.cloud', opts)

async def main():
    machine = await connect()
    
    # motor-2
    back_gantry = Gantry.from_robot(machine, "back-gantry")
    await back_gantry.home()

    while True:
        await back_gantry.move_to_position([1900], [30])
        await back_gantry.move_to_position([100], [30])

if __name__ == '__main__':
    asyncio.run(main())
