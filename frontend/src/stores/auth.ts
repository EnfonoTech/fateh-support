import { defineStore } from "pinia";
import * as authApi from "@/api/auth";
import { logout as logoutClient } from "@/api/client";
import type { Profile } from "@/types";

interface State {
  profile: Profile | null;
  loading: boolean;
  initialized: boolean;
  error: string | null;
}

export const useAuthStore = defineStore("auth", {
  state: (): State => ({
    profile: null,
    loading: false,
    initialized: false,
    error: null,
  }),
  getters: {
    isLoggedIn: (s) => !!s.profile && s.profile.user !== "Guest",
    isApprover: (s) => !!s.profile?.is_approver,
    isViewer: (s) => !!s.profile?.is_viewer,
    fullName: (s) => s.profile?.full_name || s.profile?.user || "",
  },
  actions: {
    async login(email: string, password: string) {
      this.loading = true;
      this.error = null;
      try {
        this.profile = await authApi.login(email, password);
        this.initialized = true;
      } catch (err) {
        this.error = (err as Error).message;
        throw err;
      } finally {
        this.loading = false;
      }
    },
    async refresh() {
      try {
        this.profile = await authApi.me();
      } catch {
        this.profile = null;
      } finally {
        this.initialized = true;
      }
    },
    async logout() {
      try {
        await authApi.logout();
      } finally {
        this.profile = null;
        logoutClient();
      }
    },
  },
});
