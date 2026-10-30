// Pure client-side validation helpers (mirrors backend Pydantic + DB CHECK ranges).
export const FEATURE_FIELDS = [
  ["cpu_util", "CPU utilisation (%)", 0, 100, 1], ["mem_util", "Memory utilisation (%)", 0, 100, 1],
  ["latency_ms", "Latency (ms)", 0, 10000, 0.1], ["jitter_ms", "Jitter (ms)", 0, 5000, 0.1],
  ["packet_loss_pct", "Packet loss (%)", 0, 100, 0.01], ["throughput_mbps", "Throughput (Mbps)", 0, 400000, 1],
  ["crc_errors", "CRC errors", 0, 10000000, 1], ["lsp_flaps", "LSP flaps", 0, 100000, 1], ["bgp_flaps", "BGP flaps", 0, 100000, 1],
];
export const FEATURE_DEFAULTS = { cpu_util: 35, mem_util: 55, latency_ms: 12, jitter_ms: 1.2, packet_loss_pct: 0.02, throughput_mbps: 4200, crc_errors: 0, lsp_flaps: 0, bgp_flaps: 0 };
const COUNTERS = ["crc_errors", "lsp_flaps", "bgp_flaps"];

export function validateFeatures(values) {
  const errors = {};
  FEATURE_FIELDS.forEach(([k, label, min, max]) => {
    const raw = values[k];
    const v = Number(raw);
    if (raw === "" || raw === null || raw === undefined || Number.isNaN(v)) errors[k] = `${label} is required`;
    else if (v < min || v > max) errors[k] = `Must be between ${min} and ${max}`;
    else if (COUNTERS.includes(k) && !Number.isInteger(v)) errors[k] = "Must be a whole number";
  });
  return errors;
}

export const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
export const HOST_RE = /^[A-Za-z0-9][A-Za-z0-9.\-_]*$/;
export const IPV4_RE = /^(25[0-5]|2[0-4]\d|1?\d?\d)(\.(25[0-5]|2[0-4]\d|1?\d?\d)){3}$/;

export function validateDevice(f) {
  const e = {};
  if (!HOST_RE.test(f.hostname) || f.hostname.length < 2) e.hostname = "2-64 chars: letters, digits, . - _";
  if (!IPV4_RE.test(f.mgmt_ip) && !f.mgmt_ip.includes(":")) e.mgmt_ip = "Enter a valid IPv4/IPv6 address";
  if (f.vendor.trim().length < 2) e.vendor = "Vendor is required";
  if (!f.model.trim()) e.model = "Model is required";
  if (!f.site_id) e.site_id = "Select a site";
  return e;
}
