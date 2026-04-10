import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PreviewableImageFrame } from "./PreviewableImageFrame";

describe("PreviewableImageFrame", () => {
  it("opens a fullscreen preview and closes from both the close button and backdrop", () => {
    render(
      <PreviewableImageFrame src="/demo.png" alt="示例图">
        <img src="/demo.png" alt="示例图" />
      </PreviewableImageFrame>,
    );

    const trigger = screen.getByRole("button", { name: "示例图 Pratinjau layar penuh" });

    fireEvent.click(trigger);
    expect(
      screen.getByRole("dialog", { name: "示例图 Pratinjau layar penuh" }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Tutup pratinjau layar penuh" }));
    expect(
      screen.queryByRole("dialog", { name: "示例图 Pratinjau layar penuh" }),
    ).not.toBeInTheDocument();

    fireEvent.click(trigger);
    const dialog = screen.getByRole("dialog", { name: "示例图 Pratinjau layar penuh" });
    const backdrop = dialog.parentElement?.parentElement;
    expect(backdrop).not.toBeNull();

    fireEvent.click(backdrop as HTMLElement);

    expect(
      screen.queryByRole("dialog", { name: "示例图 Pratinjau layar penuh" }),
    ).not.toBeInTheDocument();
  }, 10_000);
});
