import { FEATURE_DEFAULTS, validateDevice, validateFeatures, EMAIL_RE } from "../lib/validation";

test("default telemetry features are valid", () => {
  expect(validateFeatures(FEATURE_DEFAULTS)).toEqual({});
});

test("out-of-range and missing telemetry values are rejected", () => {
  const errors = validateFeatures({ ...FEATURE_DEFAULTS, cpu_util: 150, latency_ms: "", lsp_flaps: 1.5 });
  expect(errors.cpu_util).toMatch(/between 0 and 100/);
  expect(errors.latency_ms).toMatch(/required/);
  expect(errors.lsp_flaps).toMatch(/whole number/);
});

test("device validation catches bad hostname and IP", () => {
  const errors = validateDevice({ hostname: "-bad host", mgmt_ip: "999.1.1.1", vendor: "C", model: "", site_id: "" });
  expect(Object.keys(errors).sort()).toEqual(["hostname", "mgmt_ip", "model", "site_id", "vendor"]);
  expect(validateDevice({ hostname: "pe1-edge", mgmt_ip: "10.0.0.1", vendor: "Cisco", model: "ASR", site_id: 1 })).toEqual({});
});

test("email pattern", () => {
  expect(EMAIL_RE.test("engineer@mpls.local")).toBe(true);
  expect(EMAIL_RE.test("not-an-email")).toBe(false);
});
