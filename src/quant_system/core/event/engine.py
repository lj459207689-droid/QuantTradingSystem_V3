import logging
from queue import Empty, Queue
from threading import Thread
from typing import Callable, Dict, List

from .event import Event, EventType

HandlerType = Callable[[Event], None]
logger = logging.getLogger("EventEngine")


class EventEngine:
    """事件驱动引擎 (核心处理队列)"""

    def __init__(self, queue_timeout: float = 1.0):
        self._queue: Queue = Queue()
        self._active: bool = False
        self._thread: Thread = Thread(target=self._run, name="EventEngineThread")
        self._handlers: Dict[EventType, List[HandlerType]] = {}
        self._queue_timeout: float = queue_timeout

    def start(self) -> None:
        """启动事件引擎处理线程"""
        if not self._active:
            self._active = True
            self._thread.start()
            logger.info("事件驱动引擎已启动")

    def stop(self) -> None:
        """停止事件驱动引擎"""
        if self._active:
            self._active = False
            if self._thread.is_alive():
                self._thread.join()
            logger.info("事件驱动引擎已停止")

    def _run(self) -> None:
        """事件循环主逻辑"""
        while self._active:
            try:
                event: Event = self._queue.get(block=True, timeout=self._queue_timeout)
                self._process(event)
            except Empty:
                pass

    def _process(self, event: Event) -> None:
        """派发事件给所有 Handler"""
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"处理事件 [{event.type}] 抛出异常: {e}", exc_info=True)

    def register(self, event_type: EventType, handler: HandlerType) -> None:
        """注册事件监听"""
        handler_list = self._handlers.setdefault(event_type, [])
        if handler not in handler_list:
            handler_list.append(handler)

    def unregister(self, event_type: EventType, handler: HandlerType) -> None:
        """取消事件监听"""
        if event_type in self._handlers:
            handler_list = self._handlers[event_type]
            if handler in handler_list:
                handler.remove(handler)
            if not handler_list:
                self._handlers.pop(event_type)

    def put(self, event: Event) -> None:
        """推送新事件"""
        self._queue.put(event)
