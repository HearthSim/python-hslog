from hslog.live.export import LiveEntityTreeExporter
from hslog.packets import PacketTree


class LivePacketTree(PacketTree):
    
    def __init__(self, ts, parser):
        self.parser = parser
        self.liveExporter = LiveEntityTreeExporter(self)
        super(LivePacketTree, self).__init__(ts)
    
    def live_export(self, packet):
        return self.liveExporter.export_packet(packet)