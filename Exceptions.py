class TypeNotRightException(Exception):
    pass


class AddressNotSpecified(Exception):
    pass


class ClosedException(Exception):
    pass


class StatusException(Exception):
    pass


class RemoteAddressNotSpecified(Exception):
    pass


class PortNotSignedUpException(Exception):
    pass


class PortAlreadyInUse(Exception):
    pass

class TTLIsZeroException(Exception):
    pass

class ChecksumErrorException(Exception):
    pass

class CannotEstablishConnection(Exception):
    pass

# todo different  ICMP Exception
class TTLExpiredException(Exception):
    pass
class PortUnreachableException(Exception):
    pass
class HostUnreachableException(Exception):
    pass
class ProtocolUnreachableException(Exception):
    pass