import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "org.littletonrobotics.advantagescout2",
  appName: "Advantage Scout 2",
  webDir: "dist",
  android: {
    allowMixedContent: true,
  },
};

export default config;
