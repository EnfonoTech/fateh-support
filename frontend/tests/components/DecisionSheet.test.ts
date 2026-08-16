import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import { createI18n } from "vue-i18n";
import DecisionSheet from "@/components/DecisionSheet.vue";
import en from "@/i18n/en.json";

const i18n = createI18n({ legacy: false, locale: "en", messages: { en } });

// The sheet renders through `<teleport to="body">`, so its markup never lands
// in the wrapper's own subtree — every query has to go through document.body.
function inBody<T extends Element>(selector: string): T {
  const el = document.body.querySelector<T>(selector);
  if (!el) throw new Error(`no element matched ${selector}`);
  return el;
}

async function flush(): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, 0));
}

describe("DecisionSheet", () => {
  it("blocks reject without a note", async () => {
    const wrapper = mount(DecisionSheet, {
      props: { open: true, action: "reject" },
      global: { plugins: [i18n] },
      attachTo: document.body,
    });
    inBody<HTMLButtonElement>("button.danger").click();
    await flush();
    expect(wrapper.emitted("confirm")).toBeUndefined();
    expect(document.body.querySelector(".text-danger")?.textContent).toContain("note");
    wrapper.unmount();
  });

  it("emits confirm with trimmed note on approve", async () => {
    const wrapper = mount(DecisionSheet, {
      props: { open: true, action: "approve" },
      global: { plugins: [i18n] },
      attachTo: document.body,
    });
    const textarea = inBody<HTMLTextAreaElement>("textarea");
    textarea.value = "  looks fine  ";
    textarea.dispatchEvent(new Event("input"));
    await flush();
    inBody<HTMLButtonElement>("button.primary").click();
    await flush();
    expect(wrapper.emitted("confirm")?.[0]).toEqual(["looks fine"]);
    wrapper.unmount();
  });
});
