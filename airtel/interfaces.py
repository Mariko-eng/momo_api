'''
In Python, the abc (Abstract Base Classes) module provides a way to define abstract base classes.
An abstract base class is a class that cannot be instantiated and is meant to be subclassed by concrete classes. 
It defines a common interface that all its subclasses must implement.
'''

'''
The abstractmethod decorator is used to declare abstract methods within an abstract base class. 
Subclasses must implement these abstract methods.
'''

from abc import ABC


class BaseAirtelAuth(ABC):
    """
        Represents a momo product
    """

    def generate_access_token(self):
        """
            generate access token
        """
        pass

    def pin_encryption(self, pin):
        """
            Must encrypt pin before sending it in the body
        """
        pass

    def is_valid_callback_request(self, request_data, hash_msg) -> bool:
        """
            authenticate the callback request sent
        """
        pass
