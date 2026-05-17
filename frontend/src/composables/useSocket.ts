import { onMounted, onUnmounted } from "vue";
import { io, type Socket } from "socket.io-client";
import { useApprovalsStore } from "@/stores/approvals";
import { getCredentials } from "@/api/client";
import { isNative } from "@/utils/platform";

let socket: Socket | null = null;

function buildSocket(): Socket {
  if (socket) return socket;
  const auth: Record<string, string> = {};
  if (isNative()) {
    const c = getCredentials();
    if (c) {
      auth["api_key"] = c.apiKey;
      auth["api_secret"] = c.apiSecret;
    }
  }
  socket = io("/", {
    path: "/socketio",
    withCredentials: !isNative(),
    auth,
    transports: ["websocket", "polling"],
    reconnection: true,
    reconnectionDelay: 1000,
  });
  return socket;
}

export function useApprovalSocket() {
  const approvals = useApprovalsStore();

  function handler(payload: { name: string; status: string }) {
    approvals.applyRealtime(payload);
  }

  function reconnectSync() {
    void approvals.load(true);
    void approvals.refreshPending();
  }

  onMounted(() => {
    const s = buildSocket();
    s.on("fateh_approval_update", handler);
    s.on("connect", reconnectSync);
  });

  onUnmounted(() => {
    if (socket) {
      socket.off("fateh_approval_update", handler);
      socket.off("connect", reconnectSync);
    }
  });
}

export function disconnectSocket() {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
}
