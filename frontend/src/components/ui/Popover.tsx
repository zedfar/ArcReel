import { createPortal } from "react-dom";
import { useAnchoredPopover } from "@/hooks/useAnchoredPopover";
import { UI_LAYERS } from "@/utils/ui-layers";
import type { RefObject, ReactNode, CSSProperties } from "react";

// ---------------------------------------------------------------------------
// Popover — 统一弹出Panel原语
// ---------------------------------------------------------------------------
// 所有弹出Panel必须使用此组件，而非Manual组合 createPortal + useAnchoredPopover。
// 它通过 portal 脱离父级层叠上下文（如 header 的 backdrop-blur），
// 保证Latar belakang不Transparan并统一 z-index Manajemen。

/** PanelDefaultLatar belakang色（gray-900 = rgb(17 24 39)） */
export const POPOVER_BG = "rgb(17 24 39)";

type PopoverAlign = "start" | "center" | "end";
type PopoverLayer = keyof typeof UI_LAYERS;

interface PopoverProps {
  open: boolean;
  onClose?: () => void;
  anchorRef: RefObject<HTMLElement | null>;
  children: ReactNode;
  /** Tailwind width class, e.g. "w-72", "w-96" */
  width?: string;
  /** 额外 className（追加到Panel根元素） */
  className?: string;
  /** 额外内联Gaya */
  style?: CSSProperties;
  /** 锚点偏移量（px），Default 8 */
  sideOffset?: number;
  /** Alignment方式，Default "end" */
  align?: PopoverAlign;
  /** z-index 层级，Default "workspacePopover" */
  layer?: PopoverLayer;
  /** KustomLatar belakang色，Default POPOVER_BG */
  backgroundColor?: string;
}

export function Popover({
  open,
  onClose,
  anchorRef,
  children,
  width = "w-72",
  className = "",
  style,
  sideOffset = 8,
  align,
  layer = "workspacePopover",
  backgroundColor = POPOVER_BG,
}: PopoverProps) {
  const { panelRef, positionStyle } = useAnchoredPopover({
    open,
    anchorRef,
    onClose,
    sideOffset,
    align,
  });

  if (!open || typeof document === "undefined") return null;

  return createPortal(
    <div
      ref={panelRef}
      className={`fixed isolate ${width} ${UI_LAYERS[layer]} ${className}`}
      style={{
        ...positionStyle,
        backgroundColor,
        ...style,
      }}
    >
      {children}
    </div>,
    document.body,
  );
}
