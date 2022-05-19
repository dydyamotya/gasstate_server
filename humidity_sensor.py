from pymodbus.client.sync import ModbusSerialClient


class HumiditySensor:
    def __init__(self, unit_num: int):
        self.unit_num = unit_num

    def read_temperature_and_humidity(self, ser: ModbusSerialClient):
        temperature, humidity = struct.unpack("<ff", struct.pack("<HHHH", *ser.read_input_registers(0, 4,
                                                                                                    unit=self.unit_num).registers))
        return temperature, humidity

    def read_absolute_humidity(self, ser: ModbusSerialClient):
        temperature, humidity = self.read_temperature_and_humidity(ser)

        ew_t = 6.112 * math.exp(17.62 * temperature / (243.12 + temperature))
        p = 101325 / 100  # in gPa
        ew_tp = (1.0016 + 3.15e-6 * p - 0.074 / p) * ew_t  # in gPa

        e = humidity / 100 * ew_tp  # in gPa
        return e * 100 / 461.5 / (temperature + 273.15)  # in kg/m3
