import typing

from pymodbus.client.sync import ModbusSerialClient


class GasMixException(Exception):
    pass


class GasMix:
    def __init__(self,  unit_num: int, port: typing.Optional[str] = None, client: ModbusSerialClient = None):
        if client:
            self.ser = client
        else:
            try:
                self.ser = ModbusSerialClient(port=port, method="rtu", baudrate=19200)
            except Exception as e:
                raise GasMixException(e)
            else:
                self.unit = unit_num

    def open_valve(self, valve_number: int):
        self.ser.write_coil(valve_number, 0xFF00, unit=self.unit)

    def open_valve_close_others(self, valve_number: int):
        values = [0, ] * 16
        values[valve_number] = 1
        self.ser.write_coils(0x0000, values=values, unit=self.unit)

    def open_valves(self, valves_numbers):
        values = [0, ] * 16
        for valve_num in valves_numbers:
            values[valve_num] = 1
        self.ser.write_coils(0x0000, values=values, unit=self.unit)

    def close_all_valves(self):
        self.ser.write_coils(0x0000, values=(0,) * 16, unit=self.unit)

    def set_port(self, port: str):
        self.ser.port = port

    def close(self):
        self.ser.close()
