import asyncio

from threading import Event
from abc import ABC, abstractmethod
from typing import Mapping, Optional, Sequence
from typing_extensions import Self

from viam.module.module import Module
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.services.generic import Generic
from viam.components.motor import Motor
from viam.utils import ValueTypes
from viam import logging
from viam.resource.easy_resource import EasyResource

LOGGER = logging.getLogger(__name__)


class StartStopLoopService(ABC):
    task = None
    event = Event()
    config: ComponentConfig = None
    dependencies: Mapping[ResourceName, ResourceBase] = None
    auto_start = False

    def start(self):
        # self.on_start()
        loop = asyncio.get_event_loop()
        self.task = loop.create_task(self.looper())
        self.event.clear()

    def stop(self):
        # self.on_stop()
        self.event.set()
        if self.task is not None:
            self.task.cancel()

    async def looper(self):
        while not self.event.is_set():
            await self.on_loop()
            await asyncio.sleep(0)  # Yield control to the event loop

    @abstractmethod
    async def on_loop(self):
        """Method must be implemented by service implementation."""
        pass

    # @abstractmethod
    # async def on_start(self):
    #     """Method must be implemented by service implementation."""
    #     pass

    # @abstractmethod
    # async def on_stop(self):
    #     """Method must be implemented by service implementation."""
    #     pass

    @classmethod
    def new(
        cls,
        config: ComponentConfig,
        dependencies: Mapping[ResourceName, ResourceBase],
        auto_start=False,
    ) -> Self:
        start_stop_service = cls(config.name)
        start_stop_service.auto_start = auto_start
        start_stop_service.reconfigure(config, dependencies)
        return start_stop_service

    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        LOGGER.info("Reconfiguring")
        self.stop()
        self.config = config
        self.dependencies = dependencies
        if self.auto_start:
            self.start()

    async def do_command(
        self,
        command: Mapping[str, ValueTypes],
        *,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Mapping[str, ValueTypes]:
        LOGGER.info(f"do_command called with: {command}")
        result = {key: False for key in command.keys()}
        for name, args in command.items():
            if name == "start":
                self.start()
                result[name] = True
            if name == "stop":
                self.stop()
                result[name] = True
        return result

    def __del__(self):
        self.stop()


class ExampleService(StartStopLoopService, Generic, EasyResource):
    MODEL = "michaellee1019:startstopservice:example"

    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> "ExampleService":
        return super().new(
            config,
            dependencies,
            # Set this to True if you want your do_loop to start automatically
            auto_start=True,
        )

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        return None

    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        LOGGER.info("reconfigure called")
        super().reconfigure(config, dependencies)

    # Calling do_command with "start/stop" to control do_loop
    # {"stop": true} will stop running do_loop on next loop
    # {"start": true} will start running do_loop if not running already
    async def do_command(
        self,
        command: Mapping[str, ValueTypes],
        *,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Mapping[str, ValueTypes]:
        LOGGER.info("do_command called with command: {command}")
        return await super().do_command(command=command, timeout=timeout, **kwargs)

    async def on_loop(self):
        LOGGER.info("on_loop called.")
        asyncio.sleep(1)


class MotorRevolutionsOscillation(StartStopLoopService, Generic, EasyResource):
    MODEL = "michaellee1019:kinetic-art-service:motor-revolutions-oscillation"

    motor: Motor
    rpm: float
    revolutions: float
    secs_between_loop: int
    secs_between_reverse: int
    home_on_start = True

    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> "ExampleService":
        return super().new(
            config,
            dependencies,
            # Set this to True if you want your do_loop to start automatically
            auto_start=True,
        )

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        LOGGER.info("validating config...")
        if (
            "rpm" not in config.attributes.fields
            or "revolutions" not in config.attributes.fields
        ):
            raise Exception(
                "rpm and revolutions attributes are required for motor-revolutions-oscillation component."
            )
        return None

    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        motor_dep = next(iter(dependencies.values()))
        if motor_dep is None or motor_dep.SUBTYPE != Motor.SUBTYPE:
            raise Exception(
                "A motor is needed as a dependency to for motor-revolutions-oscillation. Make sure a motor is added as a dependency and is of the Motor type."
            )
        self.motor = motor_dep

        self.rpm = config.attributes.fields["rpm"].number_value
        self.revolutions = config.attributes.fields["revolutions"].number_value

        # These are optional and will default to sleeping 0 secs
        self.secs_between_loop = int(
            config.attributes.fields["secs_between_loop"].number_value
        )
        self.secs_between_reverse = int(
            config.attributes.fields["secs_between_reverse"].number_value
        )
        if "home_on_start" in config.attributes.fields:
            self.home_on_start = bool(
                config.attributes.fields["home_on_start"].bool_value
            )

        super().reconfigure(config, dependencies)

    # Calling do_command with "start/stop" to control do_loop
    # {"stop": true} will stop running do_loop on next loop
    # {"start": true} will start running do_loop if not running already
    async def do_command(
        self,
        command: Mapping[str, ValueTypes],
        *,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Mapping[str, ValueTypes]:
        return await super().do_command(command=command, timeout=timeout, **kwargs)

    async def on_loop(self):
        # TODO: Make on_start/on_stop methods to support logic like this instead of adding it here.
        if self.home_on_start:
            position = await self.motor.get_position()
            if position != 0:
                LOGGER.info("homing motor to position 0...")
                await self.motor.go_to(rpm=self.rpm, position_revolutions=0)
        await asyncio.sleep(self.secs_between_loop)
        LOGGER.info("moving forward")
        await self.motor.go_for(rpm=self.rpm, revolutions=self.revolutions)
        await asyncio.sleep(self.secs_between_reverse)
        LOGGER.info("moving backward")
        await self.motor.go_for(rpm=self.rpm, revolutions=-self.revolutions)

if __name__ == "__main__":
    asyncio.run(Module.run_from_registry())
