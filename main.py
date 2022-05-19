from pymodbus.client.sync import ModbusSerialClient
import socketserver
import serial
from rrg20 import RRG20_modbus
import json
from gasmix import GasMix
from humidity_sensor import HumiditySensor
import argparse


rrg_addresses = [1, 2, 3, 4, 5, 6, 7]
rrg_maxflows = [15, 15, 15, 15, 15, 600, 600]
hum_address = 12
relay_address = 11

class MyTCPHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print("{} wrote:".format(self.client_address[0]))
        print(self.data)
        try:
            gasstate = int(self.data.decode("utf-8"))
        except:
            print("Wrong state num")
        else:
            self.server.set_state(gasstate)

        # just send back the same data, but upper-cased
        # self.request.sendall(self.data.upper())

class GasStateServer(socketserver.TCPServer):
    def __init__(self, config_states, modbus_port, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_states_dict = config_states
        self.modbus_client = ModbusSerialClient(method='rtu',
                port=modbus_port,
                baudrate=19200,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE)

        self.rrgs = [RRG20_modbus(address, maxflow, client=self.modbus_client) for address, maxflow in zip(rrg_addresses, rrg_maxflows)]
        self.hum_sensor = HumiditySensor(hum_address)
        self.relay = GasMix(relay_address, client=self.modbus_client)
        self.set_state("0")
        print(self.config_states_dict)
        self.set_flag = False

    def service_actions(self):
        if self.set_flag:
            # Durachok defense
            # ============
            corrected_list = list(self.current_gasstate_list[1])
            flow_6 = self.current_gasstate_list[0][5]
            flow_7 = self.current_gasstate_list[0][6]
            if flow_6 < flow_7:
                corrected_list[6] = 1
            else:
                corrected_list[6] = 0
            # ============
            try:
                for rrg, flow in zip(self.rrgs, self.current_gasstate_list[0]):
                    rrg.write_flow(flow)
                self.relay.open_valves(corrected_list)
            except:
                pass
            finally:
                self.set_flag = False
        else:
            data = [rrg.read_flow() for rrg in self.rrgs]
            data.append(self.hum_sensor.read_temperature_and_humidity(self.modbus_client))
            print(data)

    def set_state(self, new_state: int):
        self.current_gasstate = str(new_state)
        self.current_gasstate_list = self.config_states_dict[self.current_gasstate]
        self.set_flag = True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--comport", action="store")
    args = parser.parse_args()

    HOST, PORT = "localhost", 5000

    with open("config.json") as fd:
        config_states = json.load(fd)

    # Create the server, binding to localhost on port 9999
    with GasStateServer(config_states, args.comport, (HOST, PORT), MyTCPHandler) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        server.serve_forever()


if __name__ == "__main__":
    main()

