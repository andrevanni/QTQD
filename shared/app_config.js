(function () {
  const runtimeConfigKey = "qtqd_runtime_config_v1";
  const adminTokenStorageKey = "qtqd_admin_token_v1";
  let persisted = {};

  try {
    persisted = JSON.parse(localStorage.getItem(runtimeConfigKey) || "{}");
  } catch {
    persisted = {};
  }

  const origin = window.location.origin && window.location.origin !== "null" ? window.location.origin : "";
  const defaults = {
    projectName: "QTQD",
    mode: origin ? "api" : "simulation",
    apiBaseUrl: origin ? `${origin}/api/v1` : "http://localhost:8000/api/v1",
    healthUrl: origin ? `${origin}/health` : "http://localhost:8000/health",
    tenantId: "",
    runtimeConfigKey,
    adminTokenStorageKey,
  };

  const config = { ...defaults, ...persisted };
  config.isApiMode = function isApiMode() {
    return config.mode === "api";
  };

  window.QTQD_APP_CONFIG = config;
})();
