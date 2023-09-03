class AddressInfo:
    def __init__(self, ip: str, port: int) -> None:
        self.__ip = ip
        self.__port = port

    @property
    def ip(self) -> str:
        return self.__ip
    
    @ip.setter
    def ip(self, value: str) -> None:
        self.__ip = value

    @property
    def port(self) -> int:
        return self.__port
    
    @port.setter
    def port(self, value: int) -> None:
        self.__port = value

    def values(self) -> tuple[str, int]:
        return (self.__ip, self.__port)

    def __eq__(self, other: 'AddressInfo') -> bool:
        return self.__ip == other.ip and self.__port == other.port
    
    def __hash__(self) -> int:
        return hash((self.__ip, self.__port))
    
    def __repr__(self) -> str:
        return f"AddressInfo(ip={self.__ip}, port={self.__port})"
