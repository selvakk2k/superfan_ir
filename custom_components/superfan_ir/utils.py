import io
import base64
from struct import unpack

try:
    from infrared_protocols.commands import Command
except ImportError:
    class Command:
        """Fallback Command class when infrared_protocols is not installed."""
        def __init__(self, modulation: int = 38000) -> None:
            self.modulation = modulation

class RawIRCommand(Command):
    """A raw IR command that takes a list of durations (in microseconds)."""
    
    def __init__(self, raw_timings: list[int], modulation: int = 38000) -> None:
        """Initialize the Raw IR command with alternating positive and negative durations."""
        super().__init__(modulation=modulation)
        self._raw_timings = []
        for i, t in enumerate(raw_timings):
            if i % 2 == 0:
                self._raw_timings.append(t)  # Pulse (high)
            else:
                self._raw_timings.append(-t) # Space (low)

    def get_raw_timings(self) -> list[int]:
        """Get raw timings for the command."""
        return self._raw_timings

def decode_tuya_to_raw(tuya_code_string: str) -> list[int]:
    '''
    Decodes a Tuya IR code string into a raw IR signal (list of durations).
    These codes are plain base64 encoded little-endian uint16 arrays.
    '''
    # Strip any prefix like "b64:" if present
    if tuya_code_string.startswith("b64:"):
        tuya_code_string = tuya_code_string[4:]
        
    payload_bytes = base64.b64decode(tuya_code_string)

    ir_signal_durations = []
    buffer = memoryview(payload_bytes)
    for i in range(0, len(payload_bytes), 2):
        if i + 2 <= len(payload_bytes):
            ir_signal_durations.append(unpack('<H', buffer[i:i+2])[0])
    return ir_signal_durations
