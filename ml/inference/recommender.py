"""Maps the dominant anomalous signal to an advisory recommendation (never a guaranteed fix)."""

DISCLAIMER = ("Advisory only: validate against current topology, change-management policy and vendor guidance "
              "before acting. This is not a guaranteed resolution.")

PLAYBOOK = {
    "packet_loss_pct": ("INSPECT_PATH_LOSS", "Inspect LSP path for packet loss",
                        "Packet loss is elevated. Check interface counters, optics levels and QoS drops along the LSP path."),
    "crc_errors": ("CHECK_PHYSICAL_LINK", "Check physical link and optics",
                   "CRC errors indicate possible physical-layer degradation (cabling, optics or port)."),
    "lsp_flaps": ("REVIEW_LSP_STABILITY", "Review RSVP-TE/LDP and IGP adjacency stability",
                  "Repeated LSP flaps suggest control-plane instability; review IGP adjacencies and signalling logs."),
    "bgp_flaps": ("REVIEW_BGP_SESSIONS", "Review BGP/VPNv4 session stability",
                  "BGP session flaps can disrupt L3VPN reachability; review peer logs, timers and route-reflector health."),
    "latency_ms": ("ASSESS_CONGESTION", "Assess congestion and consider TE re-optimisation",
                   "Latency is elevated, which often accompanies congestion; review utilisation and TE path options."),
    "jitter_ms": ("ASSESS_CONGESTION", "Assess queueing and jitter on the path",
                  "Jitter is elevated; review queue depths and QoS policy for latency-sensitive classes."),
    "cpu_util": ("CHECK_CONTROL_PLANE_LOAD", "Check control-plane CPU load",
                 "CPU utilisation is high; identify top processes and verify CoPP policies."),
    "mem_util": ("CHECK_MEMORY_PRESSURE", "Check memory pressure",
                 "Memory utilisation is high; check for leaks, large routing tables or excessive logging."),
    "throughput_mbps": ("REVIEW_TRAFFIC_PROFILE", "Review traffic profile",
                        "Throughput deviates from the usual envelope; confirm whether the change is expected."),
}
PRIORITY = {"low": "low", "medium": "medium", "high": "high", "critical": "urgent"}


def recommend(result: dict) -> dict:
    if result["label"] == "normal" or not result["signals"]:
        return {"action_code": "CONTINUE_MONITORING", "title": "Continue routine monitoring",
                "rationale": f"No significant deviation detected. {DISCLAIMER}", "priority": "low"}
    top = result["signals"][0]
    code, title, why = PLAYBOOK[top["feature"]]
    if result["label"] == "uncertain":
        title = f"Verify: {title.lower()}"
        why = f"Result is uncertain; gather more samples before intervening. {why}"
    return {"action_code": code, "title": title, "rationale": f"{why} {DISCLAIMER}",
            "priority": PRIORITY[result["risk_level"]]}
