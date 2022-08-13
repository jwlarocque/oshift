import _bleio
from adafruit_ble.services import Service
from adafruit_ble.uuid import VendorUUID
from adafruit_ble.attributes import Attribute
from adafruit_ble.characteristics import Characteristic, StructCharacteristic
from adafruit_ble.characteristics.int import Uint8Characteristic
from adafruit_ble.characteristics.stream import StreamOut, StreamIn

# modified from adafruit_ble nordic UARTService

VENDOR_UUID = "23B54B42-6788-48C8-BB09-316763514760"
REQUEST_UUID = "8211C95A-D6E2-4C1C-BC73-B45FBEC6C4CD"
RESPONSE_UUID = "379A12D8-254C-4F86-94B5-291189B8CF77"


class OShiftService(Service):
    """Service for receiving commands from a remote."""

    uuid = VendorUUID(VENDOR_UUID)

    request = Characteristic(
        uuid=VendorUUID(REQUEST_UUID),
        properties=Characteristic.WRITE,
        read_perm=Attribute.OPEN,
        write_perm=Attribute.OPEN,
        max_length=20,
        fixed_length=True
    )
    response = Characteristic(
        uuid=VendorUUID(RESPONSE_UUID),
        properties=Characteristic.NOTIFY,
        read_perm=Attribute.OPEN,
        write_perm=Attribute.OPEN,
        max_length=20,
        fixed_length=True
    )

    def __init__(self, *, service=None):
        super().__init__(service=service)
        self._command_buf = None
