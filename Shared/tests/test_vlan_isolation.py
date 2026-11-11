#!/usr/bin/env python3
"""Automated tests for 802.1Q VLAN Isolation and Network Zone Policy Matrix."""
import json
import os
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROUTER_PROFILE_DIR = os.path.join(BASE_DIR, "contracts", "router-profile")
PROFILES_DIR = os.path.join(ROUTER_PROFILE_DIR, "profiles")


class VlanFrame:
    """Simulated IEEE 802.1Q Ethernet Frame with VLAN Tagging."""
    def __init__(self, src_mac: str, dst_mac: str, vlan_id: int, ethertype: int = 0x0800, payload: bytes = b""):
        self.tpid = 0x8100  # IEEE 802.1Q Tag Protocol Identifier
        self.vlan_id = vlan_id
        self.src_mac = src_mac.lower()
        self.dst_mac = dst_mac.lower()
        self.ethertype = ethertype
        self.payload = payload

    def is_valid_vlan(self) -> bool:
        return 1 <= self.vlan_id <= 4094


class ZoneFirewallPolicy:
    """OpenWrt / nftables Zone-Based Firewall Policy Evaluator."""
    def __init__(self, vlan_ids: dict):
        self.vlan_map = {
            vlan_ids["lan"]: "lan",
            vlan_ids["guest"]: "guest",
            vlan_ids["vendo"]: "vendo"
        }

    def zone_for_vlan(self, vlan_id: int):
        return self.vlan_map.get(vlan_id, "unknown")

    def evaluate_flow(self, src_vlan: int, dst_vlan: int, dst_port: int, authenticated: bool = False) -> tuple[bool, str]:
        src_zone = self.zone_for_vlan(src_vlan)
        dst_zone = self.zone_for_vlan(dst_vlan)

        # Unknown or invalid VLAN tags drop immediately
        if src_zone == "unknown" or dst_zone == "unknown":
            return False, "DROP: invalid_or_unmapped_vlan"

        # Intra-zone traffic within trusted LAN is permitted
        if src_zone == "lan" and dst_zone == "lan":
            return True, "ACCEPT: intra_lan"

        # Inter-zone: GUEST -> VENDO is strictly forbidden (isolate coin hardware from users)
        if src_zone == "guest" and dst_zone == "vendo":
            return False, "DROP: guest_to_vendo_isolation_violation"

        # Inter-zone: GUEST -> LAN is strictly forbidden (isolate private network from guests)
        if src_zone == "guest" and dst_zone == "lan":
            return False, "DROP: guest_to_lan_isolation_violation"

        # Inter-zone: VENDO -> GUEST is strictly forbidden
        if src_zone == "vendo" and dst_zone == "guest":
            return False, "DROP: vendo_to_guest_isolation_violation"

        # VENDO -> ROUTER (vendo service port 4455)
        if src_zone == "vendo" and dst_zone == "lan":
            # Direct access to LAN is dropped, but endpoint on port 4455 is handled
            return False, "DROP: vendo_cannot_route_to_lan"

        return False, "DROP: default_deny"

    def evaluate_router_input(self, src_vlan: int, dst_port: int) -> tuple[bool, str]:
        """Traffic destined to the OpenWrt router itself."""
        src_zone = self.zone_for_vlan(src_vlan)

        if src_zone == "vendo":
            if dst_port == 4455:
                return True, "ACCEPT: vendo_cgi_endpoint"
            return False, "DROP: vendo_management_ports_blocked"

        if src_zone == "guest":
            if dst_port in (80, 443):
                return True, "ACCEPT: captive_portal_http"
            if dst_port == 53:
                return True, "ACCEPT: captive_dns_redirect"
            return False, "DROP: guest_router_ports_blocked"

        if src_zone == "lan":
            # LAN can access SSH and Web Admin
            if dst_port in (22, 80, 443, 9090):
                return True, "ACCEPT: lan_admin_access"
            return True, "ACCEPT: lan_generic_input"

        return False, "DROP: unknown_vlan"


class TestVlanIsolation(unittest.TestCase):
    def setUp(self):
        self.profiles = {}
        for fname in os.listdir(PROFILES_DIR):
            if fname.endswith(".json"):
                with open(os.path.join(PROFILES_DIR, fname), "r", encoding="utf-8") as f:
                    p = json.load(f)
                    self.profiles[p["profile_id"]] = p

    def test_vlan_ids_conform_to_8021q(self):
        """All profile VLAN IDs must conform to IEEE 802.1Q bounds (1-4094)."""
        for pid, profile in self.profiles.items():
            vlans = profile["networking"]["default_vlan_ids"]
            for name, vid in vlans.items():
                frame = VlanFrame("00:11:22:33:44:55", "ff:ff:ff:ff:ff:ff", vid)
                self.assertTrue(frame.is_valid_vlan(), f"Profile {pid} {name} VLAN ID {vid} out of 802.1Q range")
                self.assertEqual(frame.tpid, 0x8100)

    def test_ew1200g_pro_vlan_separation(self):
        """Ruijie RG-EW1200G Pro v1.1 must strictly isolate guest from vendo and lan."""
        profile = self.profiles["ew1200g-pro"]
        vlans = profile["networking"]["default_vlan_ids"]
        fw = ZoneFirewallPolicy(vlans)

        # 1. Guest cannot reach Vendo hardware (VLAN 10 -> VLAN 20)
        allowed, reason = fw.evaluate_flow(vlans["guest"], vlans["vendo"], dst_port=80)
        self.assertFalse(allowed)
        self.assertEqual(reason, "DROP: guest_to_vendo_isolation_violation")

        # 2. Guest cannot reach LAN PC (VLAN 10 -> VLAN 1)
        allowed, reason = fw.evaluate_flow(vlans["guest"], vlans["lan"], dst_port=445)
        self.assertFalse(allowed)
        self.assertEqual(reason, "DROP: guest_to_lan_isolation_violation")

        # 3. Vendo cannot route into LAN or Guest
        allowed, _ = fw.evaluate_flow(vlans["vendo"], vlans["guest"], dst_port=80)
        self.assertFalse(allowed)
        allowed, _ = fw.evaluate_flow(vlans["vendo"], vlans["lan"], dst_port=22)
        self.assertFalse(allowed)

        # 4. Vendo can post to router vendo CGI on port 4455
        allowed, reason = fw.evaluate_router_input(vlans["vendo"], dst_port=4455)
        self.assertTrue(allowed)
        self.assertEqual(reason, "ACCEPT: vendo_cgi_endpoint")

        # 5. Vendo CANNOT access router SSH (port 22) or web admin (port 80)
        allowed, _ = fw.evaluate_router_input(vlans["vendo"], dst_port=22)
        self.assertFalse(allowed)
        allowed, _ = fw.evaluate_router_input(vlans["vendo"], dst_port=80)
        self.assertFalse(allowed)

        # 6. Guest can reach captive portal on port 80/443 and DNS on 53
        allowed, reason = fw.evaluate_router_input(vlans["guest"], dst_port=80)
        self.assertTrue(allowed)
        allowed, reason = fw.evaluate_router_input(vlans["guest"], dst_port=53)
        self.assertTrue(allowed)

        # 7. Guest CANNOT access router SSH (port 22) or admin console
        allowed, _ = fw.evaluate_router_input(vlans["guest"], dst_port=22)
        self.assertFalse(allowed)

        # 8. LAN has administrative access
        allowed, reason = fw.evaluate_router_input(vlans["lan"], dst_port=22)
        self.assertTrue(allowed)
        allowed, reason = fw.evaluate_router_input(vlans["lan"], dst_port=80)
        self.assertTrue(allowed)

    def test_all_profiles_enforce_zero_overlap(self):
        """Every profile must define distinct non-overlapping VLAN IDs."""
        for pid, profile in self.profiles.items():
            vlans = profile["networking"]["default_vlan_ids"]
            fw = ZoneFirewallPolicy(vlans)
            self.assertNotEqual(vlans["lan"], vlans["guest"], f"Profile {pid} lan == guest")
            self.assertNotEqual(vlans["guest"], vlans["vendo"], f"Profile {pid} guest == vendo")
            self.assertNotEqual(vlans["lan"], vlans["vendo"], f"Profile {pid} lan == vendo")

            # Ingress from invalid VLAN ID drops
            allowed, _ = fw.evaluate_flow(999, vlans["lan"], 80)
            self.assertFalse(allowed)


if __name__ == "__main__":
    unittest.main()
