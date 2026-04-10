import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { Router } from "wouter";
import { memoryLocation } from "wouter/memory-location";
import { API } from "@/api";
import { useConfigStatusStore } from "@/stores/config-status-store";
import { SystemConfigPage } from "@/components/pages/SystemConfigPage";
import type { GetSystemConfigResponse, ProviderInfo } from "@/types";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeConfigResponse(
  overrides?: Partial<GetSystemConfigResponse["settings"]>,
): GetSystemConfigResponse {
  return {
    settings: {
      default_video_backend: "gemini/veo-3",
      default_image_backend: "gemini/imagen-4",
      default_text_backend: "",
      text_backend_script: "",
      text_backend_overview: "",
      text_backend_style: "",
      video_generate_audio: true,
      anthropic_api_key: { is_set: true, masked: "sk-ant-***" },
      anthropic_base_url: "",
      anthropic_model: "",
      anthropic_default_haiku_model: "",
      anthropic_default_opus_model: "",
      anthropic_default_sonnet_model: "",
      claude_code_subagent_model: "",
      agent_session_cleanup_delay_seconds: 300,
      agent_max_concurrent_sessions: 5,
      ...overrides,
    },
    options: {
      video_backends: ["gemini/veo-3"],
      image_backends: ["gemini/imagen-4"],
      text_backends: [],
    },
  };
}

function makeProviders(overrides?: Partial<ProviderInfo>): { providers: ProviderInfo[] } {
  return {
    providers: [
      {
        id: "gemini",
        display_name: "Google Gemini",
        description: "Google Gemini API",
        status: "ready",
        media_types: ["image", "video", "text"],
        capabilities: [],
        configured_keys: ["api_key"],
        missing_keys: [],
        models: {},
        ...overrides,
      },
    ],
  };
}

function renderPage(path = "/app/settings") {
  const location = memoryLocation({ path, record: true });
  return render(
    <Router hook={location.hook}>
      <SystemConfigPage />
    </Router>,
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("SystemConfigPage", () => {
  beforeEach(() => {
    useConfigStatusStore.setState(useConfigStatusStore.getInitialState(), true);
    vi.restoreAllMocks();

    // Default: silence child section network calls so tests don't hang
    vi.spyOn(API, "getSystemConfig").mockResolvedValue(makeConfigResponse());
    vi.spyOn(API, "getProviders").mockResolvedValue(makeProviders());
    vi.spyOn(API, "listCustomProviders").mockResolvedValue({ providers: [] });
    vi.spyOn(API, "getProviderConfig").mockResolvedValue({
      id: "gemini",
      display_name: "Google Gemini",
      status: "ready",
      media_types: ["image", "video"],
      capabilities: [],
      fields: [],
    } as never);
    vi.spyOn(API, "listCredentials").mockResolvedValue({ credentials: [] });
    vi.spyOn(API, "getUsageStatsGrouped").mockResolvedValue({ stats: [], period: { start: "", end: "" } });
  });

  it("renders the page header", () => {
    renderPage();
    expect(screen.getByText("Pengaturan")).toBeInTheDocument();
    expect(screen.getByText("Konfigurasi Sistem & Manajemen Akses API")).toBeInTheDocument();
  });

  it("renders all 5 sidebar sections", () => {
    renderPage();
    expect(screen.getByRole("button", { name: /Agen AI/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Provider/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /ModelPilih/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Statistik Penggunaan/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Manajemen API/ })).toBeInTheDocument();
  });

  it("defaults to the Agen AI section", () => {
    renderPage();
    const agentButton = screen.getByRole("button", { name: /Agen AI/ });
    // Active sidebar item has the indigo border class applied
    expect(agentButton.className).toContain("border-indigo-500");
  });

  it("clicking Provider makes it the active section", async () => {
    renderPage();
    const providersButton = screen.getByRole("button", { name: /Provider/ });
    fireEvent.click(providersButton);
    await waitFor(() => {
      expect(providersButton.className).toContain("border-indigo-500");
    });
  });

  it("clicking ModelPilih makes it the active section", async () => {
    renderPage();
    const mediaButton = screen.getByRole("button", { name: /ModelPilih/ });
    fireEvent.click(mediaButton);
    await waitFor(() => {
      expect(mediaButton.className).toContain("border-indigo-500");
    });
  });

  it("clicking Statistik Penggunaan makes it the active section", async () => {
    renderPage();
    const usageButton = screen.getByRole("button", { name: /Statistik Penggunaan/ });
    fireEvent.click(usageButton);
    await waitFor(() => {
      expect(usageButton.className).toContain("border-indigo-500");
    });
  });

  it("shows config warning banner when there are config issues", async () => {
    // Simulate unconfigured anthropic key to trigger an issue
    vi.spyOn(API, "getSystemConfig").mockResolvedValue(
      makeConfigResponse({ anthropic_api_key: { is_set: false, masked: null } }),
    );
    vi.spyOn(API, "getProviders").mockResolvedValue(makeProviders({ status: "ready" }));

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Konfigurasi wajib berikut belum lengkap:")).toBeInTheDocument();
    });
    expect(
      screen.getByRole("button", { name: /ArcReel Agen AI API Key/ }),
    ).toBeInTheDocument();
  });

  it("does not show warning banner when config is complete", async () => {
    renderPage();

    // Give time for config status to load
    await waitFor(() => {
      expect(API.getProviders).toHaveBeenCalled();
    });

    expect(screen.queryByText("Konfigurasi wajib berikut belum lengkap:")).not.toBeInTheDocument();
  });

  it("renders the back link that navigates to projects", () => {
    renderPage();
    const link = screen.getByRole("link", { name: "Kembali ke Beranda Proyek" });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "/app/projects");
  });
});
