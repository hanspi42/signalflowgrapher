class ValueObservable(object):
    """Class allows to observe a single value"""
    def __init__(self, value):
        self.__observers = []
        self.__value = value

    def set(self, new_value):
        """ Set a new value"""
        old_value = self.__value
        self.__value = new_value
        self.__notify(old_value, new_value)

    def observe(self, observer):
        """ Register as observer of the value"""
        self.__observers.append(observer)

    def get(self):
        """ Get value of the observed value"""
        return self.__value

    def __notify(self, old_value, new_value):
        if (old_value != new_value):
            for observer in self.__observers:
                observer(old_value, new_value)


class ObjectObservable(object):
    """Class for observing object, allows receiving of different events"""

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.__observers = []

    def observe(self, observer):
        """Add an observer."""
        self.__observers.append(observer)

    def _notify(self, value):
        """Notify about a new value"""
        for observer in self.__observers:
            observer(value)

    def unobserve(self, observer):
        """Remove the observer."""
        if observer in self.__observers:
            self.__observers.remove(observer)
