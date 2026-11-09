// Types for ios.jsx.
import type { ButtonHTMLAttributes, CSSProperties, HTMLAttributes, InputHTMLAttributes, ReactNode,
              RefObject } from "react";

type Div = HTMLAttributes<HTMLElement>;

export function Symbol(p: { name: string; children?: ReactNode } & Div): JSX.Element;
export function NavBar(p: { title?: ReactNode; leading?: ReactNode; trailing?: ReactNode;
  collapsed?: boolean } & Div): JSX.Element;
export function useCollapsed(threshold?: number): boolean;
export function LargeTitle(p: { children: ReactNode } & Div): JSX.Element;
export function Controls(p: { vertical?: boolean; children: ReactNode } & Div): JSX.Element;
export function ControlButton(p: { label: string; symbol?: string; children?: ReactNode }
  & ButtonHTMLAttributes<HTMLButtonElement>): JSX.Element;

export interface TabItem { id: string; label: string; symbol?: string; icon?: ReactNode }
export function TabBar(p: { tabs: TabItem[]; selected: string; onSelect: (id: string) => void;
  label?: string; className?: string }): JSX.Element;

export function List(p: { header?: ReactNode; footer?: ReactNode; children: ReactNode } & Div): JSX.Element;
export function Row(p: { title?: ReactNode; value?: ReactNode; icon?: ReactNode; symbol?: string;
  accessory?: ReactNode; onClick?: () => void; href?: string; chevron?: boolean;
  className?: string; children?: ReactNode }): JSX.Element;

export function Switch(p: { checked: boolean; onChange?: (checked: boolean) => void; label?: string;
  disabled?: boolean } & Omit<InputHTMLAttributes<HTMLInputElement>, "onChange">): JSX.Element;
export function Segmented<T extends string>(p: { options: { value: T; label: ReactNode }[];
  value: T; onChange: (value: T) => void; label: string; className?: string }): JSX.Element;
export function Stepper(p: { value: number; onChange: (value: number) => void; label: string;
  min?: number; max?: number; step?: number }): JSX.Element;
export function Slider(p: { value: number; onChange: (value: number) => void; label: string;
  min?: number; max?: number; step?: number; leading?: ReactNode; trailing?: ReactNode }
  & Omit<InputHTMLAttributes<HTMLInputElement>, "onChange" | "value">): JSX.Element;
export function Field(p: InputHTMLAttributes<HTMLInputElement>): JSX.Element;
export function Button(p: { variant?: "plain" | "filled" | "tinted"; destructive?: boolean;
  wide?: boolean } & ButtonHTMLAttributes<HTMLButtonElement>): JSX.Element;
export function GlassButton(p: { prominent?: boolean; label?: string; symbol?: string }
  & ButtonHTMLAttributes<HTMLButtonElement>): JSX.Element;
export function Chip(p: ButtonHTMLAttributes<HTMLButtonElement>): JSX.Element;
export function PageControl(p: { count: number; index: number; onChange?: (i: number) => void;
  label?: string }): JSX.Element;

export function EmptyState(p: { symbol?: string; icon?: ReactNode; title: ReactNode;
  children?: ReactNode; action?: ReactNode; onAction?: () => void }): JSX.Element;

export interface ModalAction { label: string; role?: "cancel" | "destructive"; onPress?: () => void }
export function Sheet(p: { open: boolean; onClose: () => void; title: ReactNode;
  onConfirm?: () => void; confirmLabel?: string; cancelLabel?: string;
  confirmDisabled?: boolean; children?: ReactNode }): JSX.Element | null;
export function Alert(p: { open: boolean; title: ReactNode; message?: ReactNode;
  actions: ModalAction[]; onClose: () => void }): JSX.Element | null;
export function ActionSheet(p: { open: boolean; title?: ReactNode; message?: ReactNode;
  actions: ModalAction[]; onClose: () => void }): JSX.Element | null;

export function useModal(open: boolean, onClose: () => void, initial?: string): RefObject<HTMLDivElement>;

// Content first
type Tint = "accent" | "red" | "orange" | "yellow" | "green" | "mint" | "teal" | "cyan" | "blue"
  | "indigo" | "purple" | "pink" | "brown" | "gray" | (string & {});
type Tap = { href?: string; onClick?: () => void };
type Tinted = { tint?: Tint; className?: string; style?: CSSProperties };

export function Art(p: { symbol?: string; glyph?: ReactNode; src?: string; alt?: string; scrim?: boolean;
  className?: string }): JSX.Element;
export function Hero(p: { eyebrow?: ReactNode; title: ReactNode; children?: ReactNode; action?: ReactNode;
  onAction?: () => void; symbol?: string; glyph?: ReactNode; src?: string; alt?: string } & Tap & Tinted): JSX.Element;
export function Card(p: { title?: ReactNode; symbol?: string; icon?: ReactNode; meta?: ReactNode;
  children?: ReactNode } & Tap & Tinted): JSX.Element;
export function Metric(p: { value: ReactNode; unit?: ReactNode; label?: ReactNode; hero?: boolean;
  tinted?: boolean; className?: string }): JSX.Element;
export function Ring(p: { value: number; label: string; large?: boolean } & Tinted): JSX.Element;
export function Bars(p: { values: number[]; current?: number; labels?: ReactNode[]; label: string } & Tinted): JSX.Element;
export function Progress(p: { value: number; label: string } & Tinted): JSX.Element;
export function Badge(p: { children: ReactNode } & Tinted): JSX.Element;
export function Stats(p: { items: { label: ReactNode; value: ReactNode }[]; className?: string }): JSX.Element;
export function Tiles(p: { children: ReactNode; className?: string }): JSX.Element;
export function Tile(p: { title: ReactNode; subtitle?: ReactNode; count?: ReactNode; symbol?: string;
  icon?: ReactNode; filled?: boolean } & Tap & Tinted): JSX.Element;
export function Carousel(p: { label: string; children: ReactNode; className?: string }): JSX.Element;
export function SectionHeader(p: { title: ReactNode; action?: ReactNode; href?: string;
  onAction?: () => void; className?: string }): JSX.Element;
