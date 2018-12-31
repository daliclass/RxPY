from __future__ import annotations
import threading
from typing import Any, List

from rx.core import Observer, ObservableBase, Disposable, Scheduler
from rx.internal import DisposedException

from .anonymoussubject import AnonymousSubject
from .innersubscription import InnerSubscription


class Subject(ObservableBase, Observer):
    """Represents an object that is both an observable sequence as well
    as an observer. Each notification is broadcasted to all subscribed
    observers.
    """

    def __init__(self) -> None:
        super().__init__()

        self.is_disposed = False
        self.is_stopped = False
        self.observers: List[Observer] = []
        self.exception: Exception = None

        self.lock = threading.RLock()

    def check_disposed(self):
        if self.is_disposed:
            raise DisposedException()

    def _subscribe_core(self, observer: Observer, scheduler: Scheduler = None) -> Disposable:
        with self.lock:
            self.check_disposed()
            if not self.is_stopped:
                self.observers.append(observer)
                return InnerSubscription(self, observer)

            if self.exception:
                observer.on_error(self.exception)
                return Disposable.empty()

            observer.on_completed()
            return Disposable.empty()

    def on_completed(self) -> None:
        """Notifies all subscribed observers of the end of the
        sequence."""

        observers = None
        with self.lock:
            self.check_disposed()
            if not self.is_stopped:
                observers = self.observers[:]
                self.observers = []
                self.is_stopped = True

        if observers:
            for observer in observers:
                observer.on_completed()

    def on_error(self, error: Exception) -> None:
        """Notifies all subscribed observers with the exception.

        Keyword arguments:
        error -- The exception to send to all subscribed observers.
        """

        os = None
        with self.lock:
            self.check_disposed()
            if not self.is_stopped:
                os = self.observers[:]
                self.observers = []
                self.is_stopped = True
                self.exception = error

        if os:
            for observer in os:
                observer.on_error(error)

    def on_next(self, value: Any) -> None:
        """Notifies all subscribed observers with the value.

        Keyword arguments:
        value -- The value to send to all subscribed observers.
        """

        os = None
        with self.lock:
            self.check_disposed()
            if not self.is_stopped:
                os = self.observers[:]

        if os:
            for observer in os:
                observer.on_next(value)

    def dispose(self) -> None:
        """Unsubscribe all observers and release resources."""

        with self.lock:
            self.is_disposed = True
            self.observers = None

    @classmethod
    def create(cls, observer, observable):
        return AnonymousSubject(observer, observable)
