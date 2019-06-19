
import re

from network_insight_sdk_generic_datasources.common.utilities import merge_dictionaries
from network_insight_sdk_generic_datasources.parsers.text.pre_post_processor import PrePostProcessor
from network_insight_sdk_generic_datasources.parsers.common.block_parser import SimpleBlockParser
from network_insight_sdk_generic_datasources.parsers.common.text_parser import GenericTextParser
from network_insight_sdk_generic_datasources.parsers.common.block_parser import LineBasedBlockParser
from network_insight_sdk_generic_datasources.parsers.common.line_parser import LineTokenizer


class JuniperSRXDevicePrePostProcessor(PrePostProcessor):

    def pre_process(self, data):
        output_lines = []
        block_parser = SimpleBlockParser()
        blocks = block_parser.parse(data)
        for block in blocks:
            lines = block.splitlines()
            output_lines.append('hostname: {}'.format(lines[2].split(' ')[-1]))
            output_lines.append('name: Juniper {}'.format(lines[3].split(' ')[-1]))
            output_lines.append('os: JUNOS {}'.format(lines[4].split(' ')[-1]))
        output_lines.append('ipAddress/fqdn: 10.40.13.37')
        output_lines.append('vendor: Juniper')
        return '\n'.join(output_lines)

    def post_process(self, data):
        return [merge_dictionaries(data)]


class JuniperSwitchPortPrePostProcessor(PrePostProcessor):

    def pre_process(self, data):
        output_lines = []
        parser = LineBasedBlockParser('Physical interface:')
        blocks = parser.parse(data)
        for block in blocks:
            administrative_status = "administrativeStatus: UP"
            switch_port_mode = "switchPortMode: TRUNK"
            mtu = self.get_pattern_match(block, ".*Link-level type: .*, MTU: (.*?),")
            name = self.get_pattern_match(block, "Physical interface: (.*), Enabled.*")
            ops_status = self.get_pattern_match(block, ".*, Enabled, Physical link is (.*)")
            ops_status = "UP" if ops_status == "Up" else "DOWN"
            connected = "connected: {}".format("TRUE" if ops_status == 'UP' else "FALSE")
            hardware_address = self.get_pattern_match(block, ".*Current address: .*, Hardware address: (.*)")
            parser = LineBasedBlockParser('Logical interface')
            blocks_1 = parser.parse(block)
            for block_1 in blocks_1:
                logical_name = self.get_pattern_match(block_1, "Logical interface (.*) \(Index .*")
                name = logical_name if logical_name else name
                vlan = "vlan: {}".format(logical_name.split('.')[1]) if logical_name else "vlan"
                output_interface_name = "name: {}".format(name)
                output_operational_status = "operationalStatus: {}".format(ops_status)
                output_hardware_address = "hardwareAddress: {}".format("" if hardware_address.isalpha() else
                                                                       hardware_address)
                output_mtu = "mtu: {}".format(mtu if mtu.isdigit() else 0)
                ip_address = self.get_pattern_match(block, ".*Local: (.*), Broadcast:.*")
                if ip_address:
                    continue
                output_line = "{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n".format(output_interface_name, administrative_status,
                                                                        switch_port_mode, output_operational_status,
                                                                        output_hardware_address, output_mtu, vlan,
                                                                        connected)
                output_lines.append(output_line)
        return '\n'.join(output_lines)

    def post_process(self, data):
        result = []
        for d in data:
            temp = {}
            for i in d.split('\n'):
                val = i.split(': ')
                temp[val[0]] = val[1] if len(val) > 1 else ""
            result.append(temp)
        return result

    def get_pattern_match(self, line_block, pattern):
        match_pattern = re.compile(pattern)
        for line in line_block.splitlines():
            match = match_pattern.match(line.strip())
            if match:
                return match.groups()[0]
        return ""


class JuniperRouterInterfacePrePostProcessor(PrePostProcessor):

    def pre_process(self, data):
        output_lines = []
        skip_interface_names = [".local.", ".local..0", ".local..1", ".local..2", "fab0.0", "fab1.0", "fxp1.0",
                                "fxp2.0", "lo0.16384", "lo0.16385"]
        parser = LineBasedBlockParser('Physical interface:')
        blocks = parser.parse(data)
        for block in blocks:
            administrative_status = "administrativeStatus: UP"
            switch_port_mode = "switchPortMode: TRUNK"
            mtu = self.get_pattern_match(block, ".*Link-level type: .*, MTU: (.*?),")
            name = self.get_pattern_match(block, "Physical interface: (.*), Enabled.*")
            ops_status = self.get_pattern_match(block, ".*, Enabled, Physical link is (.*)")
            ops_status = "UP" if ops_status == "Up" else "DOWN"
            connected = "connected: {}".format("TRUE" if ops_status == 'UP' else "FALSE")
            hardware_address = self.get_pattern_match(block, ".*Current address: .*, Hardware address: (.*)")
            parser = LineBasedBlockParser('Logical interface')
            blocks_1 = parser.parse(block)
            for block_1 in blocks_1:
                logical_name = self.get_pattern_match(block_1, "Logical interface (.*) \(Index .*")
                name = logical_name if logical_name else name
                vlan = "vlan: {}".format(logical_name.split('.')[1]) if logical_name else "vlan"
                output_interface_name = "name: {}".format(name)
                output_operational_status = "operationalStatus: {}".format(ops_status)
                output_hardware_address = "hardwareAddress: {}".format("" if hardware_address.isalpha()
                                                                       else hardware_address)
                output_mtu = "mtu: {}".format(mtu if mtu.isdigit() else 0)
                ip_address = self.get_pattern_match(block_1, ".*Local: (.*), Broadcast:.*")
                if not ip_address or name in skip_interface_names:
                    continue
                mask = self.get_pattern_match(block_1, ".*Destination: (.*), Local:.*")
                output_ip_address = "ipAddress: {}/{}".format(ip_address, mask.split('/')[1])
                output_line = "{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n".format(output_interface_name,
                                                                            administrative_status,
                                                                            switch_port_mode,
                                                                            output_operational_status,
                                                                            output_hardware_address,
                                                                            output_mtu,
                                                                            vlan, connected, output_ip_address)
                output_lines.append(output_line)
        return '\n'.join(output_lines)

    def post_process(self, data):
        result = []
        for d in data:
            temp = {}
            for i in d.split('\n'):
                val = i.split(': ')
                temp[val[0]] = val[1] if len(val) > 1 else ""
            result.append(temp)
        return result

    @staticmethod
    def get_pattern_match(line_block, pattern):
        match_pattern = re.compile(pattern)
        for line in line_block.splitlines():
            match = match_pattern.match(line.strip())
            if match:
                return match.groups()[0]
        return ""


class JuniperSRXRoutePrePostProcessor(PrePostProcessor):

    def pre_process(self, data):
        output_lines = []
        parser = LineBasedBlockParser('(.*): \d* destinations')
        blocks = parser.parse(data)
        next_hop = "Next hop: (.*) via"
        next_hop_type = ".*Next hop type: (.*?), .*"
        interface = ".* via (.*),"
        network_name_regex = "(.*) \(.* ent"
        route_type = "\*?(\w+)\s+Preference:.*"
        network_interface = "Interface: (.*)"
        rules = dict(next_hop=next_hop, next_hop_type=next_hop_type, interface=interface,
                     route_type=route_type, network_interface=network_interface)
        for block in blocks:
            vrf = self.get_pattern_match(block, '(.*): \d* destinations')
            block_parser_1 = SimpleBlockParser()
            blocks_1 = block_parser_1.parse(block)
            for block_1 in blocks_1:
                parser = LineBasedBlockParser(route_type)
                line_blocks = parser.parse(block_1)
                for idx, line_block in enumerate(line_blocks):
                    if 'inet' in line_block:
                        if 'announced' in line_block:
                            network_name = self.get_pattern_match(line_block.splitlines()[1], network_name_regex)
                        continue
                    if 'announced' in line_block:
                        network_name = self.get_pattern_match(line_block, network_name_regex)
                        continue
                    if ":" in network_name: continue  # checking skipping if interface is iv6
                    parser = GenericTextParser()
                    output = parser.parse(line_block, rules)
                    if ":" in output[0]['next_hop_type'] == "Receive": continue
                    vrf = "master" if vrf == "inet.0" else vrf.split('.inet.0')[0]
                    output_vrf = "vrf: {}".format(vrf)
                    if 'interface' in output[0].keys():
                        output_interface_name = "interfaceName: {}".format(output[0]['interface'])
                    elif 'network_interface' in output[0].keys():
                        output_interface_name = "interfaceName: {}".format(output[0]['network_interface'])
                    else:
                        continue
                    name = "name: {}_{}".format(network_name, idx)
                    output_route_type = "routeType: {}".format(output[0]['route_type'])
                    output_next_hop = "nextHop: {}".format(output[0]['next_hop'] if "next_hop" in output[0].keys()
                                                           else "DIRECT")
                    output_network = "network: {}".format(network_name)
                    output_line = "{}\n{}\n{}\n{}\n{}\n{}\n".format(output_vrf, output_network, output_route_type,
                                                                    output_next_hop, output_interface_name, name)
                    output_lines.append(output_line)
        return '\n'.join(output_lines)

    def post_process(self, data):
        result = []
        for d in data:
            temp = {}
            for i in d.split('\n'):
                val = i.split(': ')
                temp[val[0]] = val[1] if len(val) > 1 else ""
            result.append(temp)
        return result

    @staticmethod
    def get_pattern_match(line_block, pattern):
        match_pattern = re.compile(pattern)
        match = match_pattern.match(line_block.strip())
        return match.groups()[0]


class JuniperMACTablePrePostProcessor(PrePostProcessor):

    def post_process(self, data):
        result = []
        for d in data:
            temp = {}
            for i in d:
                if i == 'switchPort':
                    temp['vlan'] = d['switchPort'].split('.')[1]
                    result.append(temp)
                temp[i] = d[i]
            result.append(temp)
        return result


class JuniperSRXVRFPrePostProcessor(PrePostProcessor):

    def post_process(self, data):
        result = []
        for d in data:
            temp = {}
            vrf_name = d.keys()[0]
            router_id = [i["Router ID"] for i in d[vrf_name] if i.has_key("Router ID")]
            if "0.0.0.0" == router_id[0]: continue
            temp['name'] = "{}".format(vrf_name)
            result.append(temp)
        return result


class JuniperNeighborsTablePrePostProcessor(PrePostProcessor):

    def pre_process(self, data):
        output_lines = []
        for line in data.splitlines()[1:]:
            line_tokenizer = LineTokenizer()
            line_token = line_tokenizer.tokenize(line)
            local_interface = "localInterface: {}".format(line_token[1])
            remote_interface = "remoteInterface: {}".format(" ".join(line_token[3:-1]))
            remote_device = "remoteDevice: {}".format(line_token[-1])
            output_line = "{}\n{}\n{}\n".format(local_interface, remote_device, remote_interface)
            output_lines.append(output_line)
        return '\n'.join(output_lines)

    def post_process(self, data):
        result = []
        for d in data:
            temp = {}
            for i in d.split('\n'):
                val = i.split(': ')
                temp[val[0]] = val[1] if len(val) > 1 else ""
            result.append(temp)
        return result