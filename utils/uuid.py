import random
import sys
from uuid import UUID, uuid4 as real_uuid4

default_generator = real_uuid4

def generate_uuid():
    """
    Returns a random stringified UUID for use with older models that use char fields instead of UUID fields
    """
    return str(uuid4())


def uuid4() -> UUID:
    return default_generator()


def seeded_generator(seed: int):
    """
    Returns a UUID v4 generation function which is backed by a RNG with the given seed
    """
    rng = random.Random(seed)

    def generator() -> UUID:
        data = []
        for i in range(4):
            integer = rng.getrandbits(4 * 8)
            data.extend(integer.to_bytes(4, sys.byteorder))
        return UUID(bytes=bytes(data), version=4)

    return generator


def is_uuid(val: str) -> bool:
    try:
        UUID(val)
        return True
    except Exception:
        return False

