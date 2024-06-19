import asyncio
from typing import Mapping, Optional, Sequence
from uu import Error
from typing_extensions import Self
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.services.generic import Generic
from viam.utils import ValueTypes
from viam import logging
from threading import Thread, Event
import time
from abc import ABC, abstractmethod

LOGGER = logging.getLogger(__name__)

class StartStopLoopService(Generic, ABC):
    thread = None
    event = Event()
    config: ComponentConfig = None
    dependencies: Mapping[ResourceName, ResourceBase] = None
    auto_start = False

    def thread_run(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.looper())

    def start(self):
        if self.thread is None or not self.thread.is_alive():
            self.event.clear()
            self.thread = Thread(target=self.thread_run)
            self.thread.start()

    def stop(self):
        if self.thread is not None and self.event is not None:
            self.event.set()
            self.thread.join()
            self.thread = None

    async def looper(self):
        while not self.event.is_set():
            self.do_loop()
            await asyncio.sleep(0)  # Yield control to the event loop

    @abstractmethod
    def do_loop(self):
        """Method must be implemented by service implementation."""
        pass

    @classmethod
    def new(cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase], auto_start=False) -> Self:
        start_stop_service = cls(config.name)
        start_stop_service.auto_start = auto_start
        start_stop_service.reconfigure(config, dependencies)
        return start_stop_service

    def reconfigure(self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]):
        LOGGER.info("Reconfiguring")
        self.stop()
        self.config = config
        self.dependencies = dependencies
        if self.auto_start:
            self.start()

    async def do_command(self, command: Mapping[str, ValueTypes], *, timeout: Optional[float] = None, **kwargs) -> Mapping[str, ValueTypes]:
        LOGGER.info("do_command called")
        result = {key: False for key in command.keys()}
        for name, args in command.items():
            if name == 'start':
                self.start()
                result[name] = True
            if name == 'stop':
                self.stop()
                result[name] = True
        return result

    def __del__(self):
        self.stop()

class ExampleService(StartStopLoopService):
    MODEL = "michaellee1019:startstopservice:example"

    @classmethod
    def new(cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]) -> 'ExampleService':
        return super().new(config, dependencies, auto_start=True)

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        return None

    def reconfigure(self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]):
        LOGGER.info("reconfigure called")
        super().reconfigure(config, dependencies)

    async def do_command(self, command: Mapping[str, ValueTypes], *, timeout: Optional[float] = None, **kwargs) -> Mapping[str, ValueTypes]:
        LOGGER.info("do_command called")
        result = {key: False for key in command.keys()}
        for name, args in command.items():
            if name == 'start':
                self.start()
                result[name] = True
            if name == 'stop':
                self.stop()
                result[name] = True
        return result

    def do_loop(self):
        LOGGER.info("do_loop called.")
        time.sleep(1)
        raise Exception("asdf")