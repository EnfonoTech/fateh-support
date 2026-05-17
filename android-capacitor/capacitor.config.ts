import type { CapacitorConfig } from "@capacitor/cli";

/**
 * Fateh Trading — Capacitor v1.1 native shell.
 *
 * Strategy: remote-URL webview. The shell loads the live PWA from the
 * customer's bench (https://trading-demo.enfonoerp.com/fateh/). Cookies,
 * CSRF, Service Worker, and Frappe authentication all work out of the box
 * because the WebView origin matches the API host.
 *
 * For an air-gapped or air-restricted deployment, switch to the local
 * `webDir` mode by removing `server.url` and pointing `webDir` at a
 * pre-built bundle.
 */
const config: CapacitorConfig = {
  appId: "com.enfono.fatehtrading",
  appName: "Fateh Trading",
  webDir: "www",
  server: {
    url: "https://trading-demo.enfonoerp.com/fateh/",
    androidScheme: "https",
    cleartext: false,
    allowNavigation: ["trading-demo.enfonoerp.com", "*.enfonoerp.com"],
  },
  android: {
    backgroundColor: "#ffffff",
    allowMixedContent: false,
    captureInput: true,
    webContentsDebuggingEnabled: true,
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 600,
      backgroundColor: "#ffffff",
      androidScaleType: "CENTER_CROP",
      showSpinner: false,
    },
    StatusBar: {
      backgroundColor: "#2563EB",
      style: "LIGHT",
      overlaysWebView: false,
    },
  },
};

export default config;
