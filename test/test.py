import asyncio

from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions
from viam.components.motor import Motor
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
    motor_2 = Motor.from_robot(machine, "motor-2")

    while True:
        await motor_2.go_for(rpm=100, revolutions=10)
        await motor_2.go_for(rpm=-100, revolutions=10)
  
    # Don't forget to close the machine when you're done!
    await machine.close()

if __name__ == '__main__':
    asyncio.run(main())
