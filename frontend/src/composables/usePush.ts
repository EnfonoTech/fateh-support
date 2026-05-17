import { subscribePush, unsubscribePush } from "@/api/push";
import { useBrandingStore } from "@/stores/branding";

function urlBase64ToUint8Array(base64: string): Uint8Array {
  const padding = "=".repeat((4 - (base64.length % 4)) % 4);
  const b64 = (base64 + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(b64);
  const arr = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
  return arr;
}

export async function ensurePushSubscription(): Promise<PushSubscription | null> {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) return null;
  const branding = useBrandingStore();
  const vapidKey = branding.config.vapid_public_key;
  if (!vapidKey) return null;

  const registration = await navigator.serviceWorker.ready;
  let sub = await registration.pushManager.getSubscription();
  if (!sub) {
    try {
      const key = urlBase64ToUint8Array(vapidKey);
      const applicationServerKey = key.buffer.slice(
        key.byteOffset,
        key.byteOffset + key.byteLength
      ) as ArrayBuffer;
      sub = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey,
      });
    } catch {
      return null;
    }
  }
  try {
    await subscribePush(sub.toJSON(), "web");
  } catch {
    /* ignore; will retry on next app open */
  }
  return sub;
}

export async function requestPushPermission(): Promise<boolean> {
  if (!("Notification" in window)) return false;
  if (Notification.permission === "granted") {
    await ensurePushSubscription();
    return true;
  }
  if (Notification.permission === "denied") return false;
  const result = await Notification.requestPermission();
  if (result === "granted") {
    await ensurePushSubscription();
    return true;
  }
  return false;
}

export async function cancelPushSubscription(): Promise<void> {
  if (!("serviceWorker" in navigator)) return;
  const reg = await navigator.serviceWorker.ready;
  const sub = await reg.pushManager.getSubscription();
  if (!sub) return;
  try {
    await unsubscribePush(sub.endpoint);
  } catch {
    /* ignore */
  }
  await sub.unsubscribe();
}
