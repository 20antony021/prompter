import { setGlobalDispatcher, ProxyAgent, Agent } from "undici";
import { setDefaultResultOrder } from "node:dns";

try {
  // Prefer IPv4 to avoid IPv6 connectivity issues in restricted networks
  setDefaultResultOrder("ipv4first");
} catch {}

const proxy = process.env.HTTPS_PROXY || process.env.HTTP_PROXY || process.env.ALL_PROXY;

try {
  if (proxy) {
    const dispatcher = new ProxyAgent({
      uri: proxy,
      connect: { timeout: 30_000 },
    });
    setGlobalDispatcher(dispatcher);
  } else {
    const dispatcher = new Agent({
      connect: { timeout: 30_000 },
    });
    setGlobalDispatcher(dispatcher);
  }
} catch {}
