# ADUP Packet Formats

from scapy.packet import Packet, bind_layers
from scapy.fields import (
    BitField,
    ByteField,
    IPField,
    IntField,
    PacketListField,
    ShortField,
    XByteField,
    XShortField,
)
from scapy.layers.l2 import Ether

class ADUP_Route_Entry(Packet):
    name = "ADUP Route Entry"
    fields_desc = [
        ByteField("prefix_len", 0),
        IPField("dest_network", "0.0.0.0"),
        IntField("total_bandwidth", 0),
        IntField("total_delay", 0),
        IntField("total_jitter", 0),
        ByteField("total_packet_loss", 0),
        ByteField("total_congestion", 0),
    ]

class ADUP_Hello(Packet):
    name = "ADUP Hello Packet"
    fields_desc = [
        BitField("version", 1, 4),
        BitField("opcode", 1, 4),  # 1 for Hello
        XByteField("reserved", 0),
        ShortField("delay", 0),
        ShortField("jitter", 0),
        ByteField("packet_loss", 0),
        ByteField("congestion", 0),
        ShortField("link_stability", 0),
        XShortField("checksum", None),
    ]

class ADUP_Update(Packet):
    name = "ADUP Update Packet"
    fields_desc = [
        BitField("version", 1, 4),
        BitField("opcode", 2, 4),  # 2 for Update
        XByteField("reserved", 0),
        XShortField("checksum", None),
        PacketListField("routes", [], ADUP_Route_Entry)
    ]

class ADUP_Query(Packet):
    name = "ADUP Query Packet"
    fields_desc = [
        BitField("version", 1, 4),
        BitField("opcode", 3, 4),  # 3 for Query
        XByteField("reserved", 0),
        IPField("dest_network", "0.0.0.0"),
        ByteField("prefix_len", 0),
        IntField("feasible_distance", 0),
        XShortField("checksum", None),
    ]

class ADUP_Reply(Packet):
    name = "ADUP Reply Packet"
    fields_desc = [
        BitField("version", 1, 4),
        BitField("opcode", 4, 4),  # 4 for Reply
        XByteField("reserved", 0),
        IPField("dest_network", "0.0.0.0"),
        ByteField("prefix_len", 0),
        IntField("reported_distance", 0),
        ByteField("reachable", 1),  # 1 = reachable, 0 = unreachable
        XShortField("checksum", None),
    ]

class ADUP_Ack(Packet):
    name = "ADUP Acknowledgment Packet"
    fields_desc = [
        BitField("version", 1, 4),
        BitField("opcode", 5, 4),  # 5 for ACK
        XByteField("reserved", 0),
        IntField("sequence_number", 0),
        XShortField("checksum", None),
    ]

# Bind the layers to a custom EtherType for our protocol
bind_layers(Ether, ADUP_Hello, type=0x88B5)
bind_layers(Ether, ADUP_Update, type=0x88B6)
bind_layers(Ether, ADUP_Query, type=0x88B7)
bind_layers(Ether, ADUP_Reply, type=0x88B8)
bind_layers(Ether, ADUP_Ack, type=0x88B9)
bind_layers(Ether, ADUP_Query, type=0x88B7)
bind_layers(Ether, ADUP_Reply, type=0x88B8)
bind_layers(Ether, ADUP_Ack, type=0x88B9)

