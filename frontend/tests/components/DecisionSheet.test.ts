import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import { createI18n } from "vue-i18n";
import DecisionSheet from "@/components/DecisionSheet.vue";
import en from "@/i18n/en.json";

const i18n = createI18n({ legacy: false, locale: "en", messages: { en } });

describe("DecisionSheet", () => {
  it("blocks reject without a note", async () => {
    const wrapper = mount(DecisionSheet, {
      props: { open: true, action: "reject" },
      global: { plugins: [i18n] },
      attachTo: document.body,
    });
    await wrapper.find("button.danger").trigger("click");
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
    await wrapper.find("textarea").setValue("  looks fine  ");
    await wrapper.find("button.primary").trigger("click");
    expect(wrapper.emitted("confirm")?.[0]).toEqual(["looks fine"]);
    wrapper.unmount();
  });
});
