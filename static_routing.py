#!/usr/bin/env python3
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import hub

class StaticRoutingController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(StaticRoutingController, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.logger.info("Static Routing Controller started")
        self.monitor_thread = hub.spawn(self._monitor)

    def _monitor(self):
        while True:
            hub.sleep(10)
            for dpid, dp in self.datapaths.items():
                self.logger.info("Reinstalling rules on dpid=%s", dpid)
                if dpid == 1:
                    self._install_s1_rules(dp)
                elif dpid == 2:
                    self._install_s2_rules(dp)
                elif dpid == 3:
                    self._install_s3_rules(dp)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        dpid = datapath.id
        self.datapaths[dpid] = datapath
        self.logger.info("Switch connected: dpid=%s", dpid)
        if dpid == 1:
            self._install_s1_rules(datapath)
        elif dpid == 2:
            self._install_s2_rules(datapath)
        elif dpid == 3:
            self._install_s3_rules(datapath)

    def _add_flow(self, dp, priority, match, actions):
        ofp = dp.ofproto
        parser = dp.ofproto_parser
        inst = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=dp, priority=priority, match=match, instructions=inst)
        dp.send_msg(mod)

    def _install_s1_rules(self, dp):
        parser = dp.ofproto_parser
        ofp = dp.ofproto
        self._add_flow(dp, 20, parser.OFPMatch(eth_type=0x0800, ipv4_dst='10.0.0.1'), [parser.OFPActionOutput(1)])
        self._add_flow(dp, 20, parser.OFPMatch(eth_type=0x0800, ipv4_dst='10.0.0.2'), [parser.OFPActionOutput(2)])
        self._add_flow(dp, 10, parser.OFPMatch(eth_type=0x0800), [parser.OFPActionOutput(3)])
        self._add_flow(dp, 5, parser.OFPMatch(eth_type=0x0806), [parser.OFPActionOutput(ofp.OFPP_FLOOD)])
        self.logger.info("S1 rules installed")

    def _install_s2_rules(self, dp):
        parser = dp.ofproto_parser
        ofp = dp.ofproto
        self._add_flow(dp, 20, parser.OFPMatch(eth_type=0x0800, ipv4_dst='10.0.0.1'), [parser.OFPActionOutput(1)])
        self._add_flow(dp, 20, parser.OFPMatch(eth_type=0x0800, ipv4_dst='10.0.0.2'), [parser.OFPActionOutput(1)])
        self._add_flow(dp, 20, parser.OFPMatch(eth_type=0x0800, ipv4_dst='10.0.0.3'), [parser.OFPActionOutput(2)])
        self._add_flow(dp, 20, parser.OFPMatch(eth_type=0x0800, ipv4_dst='10.0.0.4'), [parser.OFPActionOutput(2)])
        self._add_flow(dp, 5, parser.OFPMatch(eth_type=0x0806), [parser.OFPActionOutput(ofp.OFPP_FLOOD)])
        self.logger.info("S2 rules installed")

    def _install_s3_rules(self, dp):
        parser = dp.ofproto_parser
        ofp = dp.ofproto
        self._add_flow(dp, 20, parser.OFPMatch(eth_type=0x0800, ipv4_dst='10.0.0.3'), [parser.OFPActionOutput(1)])
        self._add_flow(dp, 20, parser.OFPMatch(eth_type=0x0800, ipv4_dst='10.0.0.4'), [parser.OFPActionOutput(2)])
        self._add_flow(dp, 10, parser.OFPMatch(eth_type=0x0800), [parser.OFPActionOutput(3)])
        self._add_flow(dp, 5, parser.OFPMatch(eth_type=0x0806), [parser.OFPActionOutput(ofp.OFPP_FLOOD)])
        self.logger.info("S3 rules installed")
