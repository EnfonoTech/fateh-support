import { call } from "./client";

export function subscribePush(
  subscription: PushSubscriptionJSON,
  type: "web" | "fcm" | "apns" = "web"
): Promise<{ ok: boolean; name: string }> {
  return call("fateh_support.api.push.subscribe", {
    body: { subscription: JSON.stringify(subscription), type },
  });
}

export function unsubscribePush(endpoint: string): Promise<{ ok: boolean }> {
  return call("fateh_support.api.push.unsubscribe", { body: { endpoint } });
}
