// React components over the kit's CSS recipes.
//
// Each one renders the markup ios-components.css already styles, so the
// look is the kit's measured one and nothing here restates a size or a
// colour. What React adds is behaviour the static recipes can't have:
// a sheet that traps focus, closes on Escape and hands focus back; an
// alert that lands on the safe button; tabs that move with the arrow
// keys; rows that are real buttons for a keyboard and a screen reader.
//
// Load the CSS once, in this order:
//   import "./vendor/ios-tokens.css";
//   import "./vendor/ios-components.css";
//   import "./vendor/ios-react.css";
//
// No dependencies beyond React 18 or later. Plain JSX, so it drops into a
// JavaScript or a TypeScript project; ios.d.ts has the prop types.

import { createContext, useContext, useEffect, useId, useRef, useState } from "react";

const cx = (...names) => names.filter(Boolean).join(" ");

// ------------------------------------------------------------ Symbols

/** The slot for an SF Symbol. SF Symbols can't ship in a web kit, so the
 *  child is your stand-in drawing; the name is what an implementation on
 *  Apple platforms needs, and is the part that has to be exact. */
export function Symbol({ name, className, children, ...rest }) {
  return (
    <span className={cx("ios-symbol", className)} data-sf-symbol={name}
          aria-hidden="true" {...rest}>
      {children}
    </span>
  );
}

// Stand-ins drawn at SF Symbols' regular weight: stroke 2 on a 24 grid,
// round caps and joins.
const glyph = (d) => (
  <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor"
       strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d={d} />
  </svg>
);
const XMARK = glyph("M6 6l12 12M18 6L6 18");
const CHECKMARK = glyph("M5 12.5l4.5 4.5L19 7");

// ------------------------------------------------------------ Bars

/** collapsed: false while a LargeTitle is showing, so the bar is bare
 *  and its compact title hidden until the large one scrolls away, as on
 *  iOS. useCollapsed() gives you the value. */
export function NavBar({ title, leading, trailing, collapsed = true, className, ...rest }) {
  return (
    <nav className={cx("ios-navbar", !collapsed && "ios-navbar--at-rest", className)} {...rest}>
      {leading}
      <span className="ios-navbar__title">{title}</span>
      {trailing}
    </nav>
  );
}

/** True once the page has scrolled past the large title. */
export function useCollapsed(threshold = 24) {
  const [collapsed, setCollapsed] = useState(false);
  useEffect(() => {
    const sync = () => setCollapsed(window.scrollY > threshold);
    sync();
    window.addEventListener("scroll", sync, { passive: true });
    return () => window.removeEventListener("scroll", sync);
  }, [threshold]);
  return collapsed;
}

/** A top-level screen's large title. Without one, a top-level iOS
 *  screen reads as a web page. */
export function LargeTitle({ className, children, ...rest }) {
  return <h1 className={cx("ios-largetitle", className)} {...rest}>{children}</h1>;
}

/** The iOS 26 glass capsule that groups bar buttons. */
export function Controls({ vertical, className, children, ...rest }) {
  return (
    <div className={cx("ios-glass ios-controls", vertical && "ios-controls--vertical", className)}
         {...rest}>
      {children}
    </div>
  );
}

export function ControlButton({ label, symbol, className, children, ...rest }) {
  return (
    <button type="button" className={cx("ios-controls__item", className)}
            aria-label={label} data-sf-symbol={symbol} {...rest}>
      {children}
    </button>
  );
}

/** tabs: [{ id, label, symbol, icon }]. Arrow keys move between tabs,
 *  Home and End jump to the ends, as a tab list does. */
export function TabBar({ tabs, selected, onSelect, label = "Tabs", className }) {
  const refs = useRef([]);
  const move = (i) => {
    const n = (i + tabs.length) % tabs.length;
    refs.current[n]?.focus();
    onSelect(tabs[n].id);
  };
  const onKeyDown = (e, i) => {
    const to = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: tabs.length - 1 }[e.key];
    if (to !== undefined) {
      e.preventDefault();
      move(to);
    }
  };
  return (
    <nav className={cx("ios-tabbar", className)} role="tablist" aria-label={label}>
      {tabs.map((t, i) => (
        <button key={t.id} type="button" role="tab" ref={(el) => (refs.current[i] = el)}
                className="ios-tabbar__item" aria-selected={t.id === selected}
                tabIndex={t.id === selected ? 0 : -1}
                onClick={() => onSelect(t.id)} onKeyDown={(e) => onKeyDown(e, i)}>
          <span data-sf-symbol={t.symbol} aria-hidden="true">{t.icon}</span>
          {t.label}
        </button>
      ))}
    </nav>
  );
}

// ------------------------------------------------------------ Lists

export function List({ header, footer, className, children, ...rest }) {
  return (
    <>
      {header && <div className="ios-list__header">{header}</div>}
      <ul className={cx("ios-list", className)} {...rest}>{children}</ul>
      {footer && <div className="ios-list__footer">{footer}</div>}
    </>
  );
}

/** One row. With onClick or href it becomes tappable: a real button or
 *  link stretched over the row, so it works from a keyboard and reads as
 *  "title, value" to a screen reader, and the kit draws the chevron. */
export function Row({ title, value, icon, symbol, accessory, onClick, href, chevron,
                      className, children }) {
  const tappable = Boolean(onClick || href);
  const titleId = useId();
  const name = [title, typeof value === "string" ? value : null].filter(Boolean).join(", ");
  return (
    <li className={cx("ios-list__row", tappable && "ios-list__row--tappable", className)}>
      {(icon || symbol) && (
        <span className="ios-list__icon" data-sf-symbol={symbol} aria-hidden="true">{icon}</span>
      )}
      {title && <span className="ios-list__title" id={titleId}>{title}</span>}
      {children}
      {value != null && <span className="ios-list__value">{value}</span>}
      {accessory && <RowLabel id={titleId}>{accessory}</RowLabel>}
      {tappable && (chevron ?? true) && (
        <span className="ios-list__chevron" aria-hidden="true">&rsaquo;</span>
      )}
      {href ? (
        <a className="ios-list__action" href={href} aria-label={name} />
      ) : onClick ? (
        <button type="button" className="ios-list__action" onClick={onClick} aria-label={name} />
      ) : null}
    </li>
  );
}

// A row's control is named by the row's title, so a switch reads as
// "Daily nudge, switch, on" rather than as an unlabelled switch.
const LabelContext = createContext(null);
function RowLabel({ id, children }) {
  return <LabelContext.Provider value={id}>{children}</LabelContext.Provider>;
}

// ------------------------------------------------------------ Controls

export function Switch({ checked, onChange, label, disabled, className, ...rest }) {
  const labelledBy = useContext(LabelContext);
  return (
    <label className={cx("ios-switch", className)}>
      <input type="checkbox" role="switch" checked={checked} disabled={disabled}
             onChange={(e) => onChange?.(e.target.checked)}
             aria-label={label} aria-labelledby={label ? undefined : labelledBy ?? undefined}
             {...rest} />
      <span className="ios-switch__track" />
    </label>
  );
}

/** options: [{ value, label }]. Native radios underneath, so the arrow
 *  keys already move the selection. */
export function Segmented({ options, value, onChange, label, className }) {
  const name = useId();
  return (
    <div className={cx("ios-segmented", className)} role="radiogroup" aria-label={label}>
      {options.map((o) => (
        <label key={o.value}>
          <input type="radio" name={name} value={o.value} checked={o.value === value}
                 onChange={() => onChange(o.value)} />
          <span />
          {o.label}
        </label>
      ))}
    </div>
  );
}

export function Stepper({ value, onChange, min = -Infinity, max = Infinity, step = 1, label }) {
  return (
    <div className="ios-stepper" role="group" aria-label={label}>
      <button type="button" className="ios-stepper__btn" aria-label={`Decrease ${label}`}
              disabled={value - step < min} onClick={() => onChange(value - step)}>−</button>
      <button type="button" className="ios-stepper__btn" aria-label={`Increase ${label}`}
              disabled={value + step > max} onClick={() => onChange(value + step)}>+</button>
    </div>
  );
}

/** A native range input, so arrows, Home and End work. leading and
 *  trailing put a symbol either side, as volume and brightness do. */
export function Slider({ value, onChange, min = 0, max = 100, step = 1, label,
                         leading, trailing, className, ...rest }) {
  const percent = ((value - min) / (max - min)) * 100;
  const input = (
    <input className={cx("ios-slider", className)} type="range" min={min} max={max}
           step={step} value={value} aria-label={label}
           style={{ "--ios-slider-value": percent }}
           onChange={(e) => onChange(Number(e.target.value))} {...rest} />
  );
  if (!leading && !trailing) return input;
  return <div className="ios-slider-row">{leading}{input}{trailing}</div>;
}

export function Field({ className, ...rest }) {
  return <input className={cx("ios-field", className)} {...rest} />;
}

/** variant: "plain" (default), "filled" or "tinted". */
export function Button({ variant = "plain", destructive, wide, className, children, ...rest }) {
  return (
    <button type="button" className={cx("ios-btn",
        variant !== "plain" && `ios-btn--${variant}`,
        destructive && "ios-btn--destructive", wide && "ios-btn--wide", className)} {...rest}>
      {children}
    </button>
  );
}

/** A floating glass button, iOS 26's shape. Icon-only needs a label. */
export function GlassButton({ prominent, label, symbol, className, children, ...rest }) {
  return (
    <button type="button" aria-label={label} data-sf-symbol={symbol}
            className={cx("ios-glass ios-glass-btn", prominent && "ios-glass--prominent", className)}
            {...rest}>
      {children}
    </button>
  );
}

export function Chip({ className, children, ...rest }) {
  return <button type="button" className={cx("ios-chip", className)} {...rest}>{children}</button>;
}

/** count dots; past six they shrink toward the ends, as Apple's do. */
export function PageControl({ count, index, onChange, label = "Page" }) {
  return (
    <div className={cx("ios-pagecontrol", count === 7 && "ios-pagecontrol--seven",
                       count > 7 && "ios-pagecontrol--many")}
         role="group" aria-label={`${label} ${index + 1} of ${count}`}>
      {Array.from({ length: count }, (_, i) => (
        <button key={i} type="button" className="ios-pagecontrol__dot"
                aria-current={i === index ? "true" : undefined}
                aria-label={`${label} ${i + 1}`} onClick={() => onChange?.(i)} />
      ))}
    </div>
  );
}

// ------------------------------------------------------------ Content first

// The parts a screen opens on rather than a list: a hero, cards with a
// figure, rings, bars, tiles. See ios-components.css "Content first".
// tint is one of the system colour names (green, orange...) or any CSS
// colour; left out, the part takes the accent, which is the brand.
const TINTS = new Set(["accent", "red", "orange", "yellow", "green", "mint", "teal", "cyan",
                       "blue", "indigo", "purple", "pink", "brown", "gray"]);
function tinted(tint, style) {
  if (!tint) return { tintClass: null, style };
  if (TINTS.has(tint)) return { tintClass: `ios-tint-${tint}`, style };
  return { tintClass: null, style: { ...style, "--tint": tint } };
}

// A whole card or tile that is one tap: a real link or button laid over
// it, named by its title, so it works from a keyboard and a screen reader.
function Cover({ href, onClick, label }) {
  if (href) return <a className="ios-cover" href={href} aria-label={label} />;
  if (onClick) return <button type="button" className="ios-cover" onClick={onClick} aria-label={label} />;
  return null;
}

/** Artwork from the tint and a large symbol, or a photo (src). */
export function Art({ symbol, glyph, src, alt = "", scrim = true, className }) {
  return (
    <div className={cx("ios-art", scrim && "ios-art--scrim", className)}>
      {src ? <img className="ios-art__img" src={src} alt={alt} />
           : glyph && <span className="ios-art__glyph" data-sf-symbol={symbol} aria-hidden="true">{glyph}</span>}
    </div>
  );
}

/** The card a screen opens on: art behind, words at the foot. */
export function Hero({ eyebrow, title, children, action, onAction, symbol, glyph, src, alt,
                       tint, href, onClick, className, style }) {
  const t = tinted(tint, style);
  return (
    <div className={cx("ios-hero", t.tintClass, className)} style={t.style}>
      <Art symbol={symbol} glyph={glyph} src={src} alt={alt} />
      <Cover href={href} onClick={onClick} label={typeof title === "string" ? title : undefined} />
      {eyebrow && <p className="ios-hero__eyebrow">{eyebrow}</p>}
      <h2 className="ios-hero__title">{title}</h2>
      {children && <p className="ios-hero__body">{children}</p>}
      {action && (
        <button type="button" className="ios-btn ios-btn--filled ios-hero__action" onClick={onAction}>{action}</button>
      )}
    </div>
  );
}

/** A summary card: a header in its colour, then whatever it summarises. */
export function Card({ title, symbol, icon, meta, tint, href, onClick, className, style, children }) {
  const t = tinted(tint, style);
  return (
    <div className={cx("ios-card", t.tintClass, className)} style={t.style}>
      <Cover href={href} onClick={onClick} label={typeof title === "string" ? title : undefined} />
      {title && (
        <div className="ios-card__head">
          {(icon || symbol) && <span data-sf-symbol={symbol} aria-hidden="true">{icon}</span>}
          {title}
          {meta && <span className="ios-card__meta">{meta}</span>}
        </div>
      )}
      {children}
    </div>
  );
}

/** A figure: the value rounded and bold, its unit smaller beside it. */
export function Metric({ value, unit, label, hero, tinted: inTint, className }) {
  return (
    <div className={cx("ios-metric", hero && "ios-metric--hero", inTint && "ios-metric--tinted", className)}>
      <span className="ios-metric__value">{value}{unit && <span className="ios-metric__unit">{unit}</span>}</span>
      {label && <span className="ios-metric__label">{label}</span>}
    </div>
  );
}

/** Progress as a ring; value from 0 to 1. label is what a screen reader hears. */
export function Ring({ value, label, large, tint, className, style }) {
  const t = tinted(tint, style);
  const v = Math.max(0, Math.min(1, value)) * 100;
  return (
    <svg className={cx("ios-ring", large && "ios-ring--large", t.tintClass, className)} style={t.style}
         viewBox="0 0 40 40" role="img" aria-label={label}>
      <circle className="ios-ring__track" cx="20" cy="20" r="16" />
      <circle className="ios-ring__value" cx="20" cy="20" r="16" pathLength="100" strokeDasharray={`${v} 100`} />
    </svg>
  );
}

/** Columns at a glance; values from 0 to 1, current is the solid one. */
export function Bars({ values, current = values.length - 1, labels, label, tint, className, style }) {
  const t = tinted(tint, style);
  return (
    <div className={cx(t.tintClass, className)} style={t.style}>
      <div className="ios-bars" role="img" aria-label={label}>
        {values.map((v, i) => (
          <span key={i} style={{ "--v": v }} aria-current={i === current ? "true" : undefined} />
        ))}
      </div>
      {labels && <div className="ios-bars__labels" aria-hidden="true">{labels.map((l, i) => <span key={i}>{l}</span>)}</div>}
    </div>
  );
}

/** A single fraction, from 0 to 1. */
export function Progress({ value, label, tint, className, style }) {
  const t = tinted(tint, style);
  const pct = Math.round(Math.max(0, Math.min(1, value)) * 100);
  return (
    <div className={cx("ios-progress", t.tintClass, className)} style={t.style} role="progressbar"
         aria-label={label} aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct}>
      <span style={{ width: `${pct}%` }} />
    </div>
  );
}

/** A status in a capsule. */
export function Badge({ tint, className, style, children }) {
  const t = tinted(tint, style);
  return <span className={cx("ios-badge", t.tintClass, className)} style={t.style}>{children}</span>;
}

/** Three or four figures in a row: items [{ label, value }]. */
export function Stats({ items, className }) {
  return (
    <dl className={cx("ios-stats", className)}>
      {items.map((it, i) => <div key={i}><dt>{it.label}</dt><dd>{it.value}</dd></div>)}
    </dl>
  );
}

export function Tiles({ className, children }) {
  return <div className={cx("ios-tiles", className)}>{children}</div>;
}

/** One tile: a symbol in a coloured circle, a count, the name. */
export function Tile({ title, subtitle, count, symbol, icon, tint, filled, href, onClick, className, style }) {
  const t = tinted(tint, style);
  const label = [title, count != null ? String(count) : null].filter(Boolean).join(", ");
  return (
    <div className={cx("ios-tile", filled && "ios-tile--filled", t.tintClass, className)} style={t.style}>
      <Cover href={href} onClick={onClick} label={label} />
      <span className="ios-tile__icon" data-sf-symbol={symbol} aria-hidden="true">{icon}</span>
      {count != null && <span className="ios-tile__count">{count}</span>}
      <span className="ios-tile__title">{title}</span>
      {subtitle && <span className="ios-tile__subtitle">{subtitle}</span>}
    </div>
  );
}

/** A row that scrolls sideways and snaps, the next item peeking in. */
export function Carousel({ label, className, children }) {
  return (
    <div className={cx("ios-carousel", className)} role="region" aria-label={label} tabIndex={0}>
      {children}
    </div>
  );
}

/** A section's title, set as a title, with an action at its end. */
export function SectionHeader({ title, action, href, onAction, className }) {
  return (
    <h2 className={cx("ios-sectionhead", className)}>
      {title}
      {action && (href
        ? <a className="ios-sectionhead__action" href={href}>{action}</a>
        : <button type="button" className="ios-sectionhead__action ios-btn-reset" onClick={onAction}>{action}</button>)}
    </h2>
  );
}

// ------------------------------------------------------------ States

/** The empty and error states. Apple pins the action to the bottom of
 *  the screen rather than under the sentence; the kit does that. */
export function EmptyState({ symbol, icon, title, children, action, onAction }) {
  return (
    <div className="ios-empty">
      <div className="ios-empty__glyph" data-sf-symbol={symbol} aria-hidden="true">{icon}</div>
      <h2 className="ios-empty__title">{title}</h2>
      {children && <p className="ios-empty__body">{children}</p>}
      {action && (
        <button type="button" className="ios-btn ios-btn--filled ios-empty__action"
                onClick={onAction}>{action}</button>
      )}
    </div>
  );
}

// ------------------------------------------------------------ Modals

const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]),' +
                  ' textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

/** Shared by the sheet, the alert and the action sheet: Escape closes,
 *  Tab stays inside, the page behind doesn't scroll, and focus goes back
 *  to whatever opened it. */
function useModal(open, onClose, initial) {
  const ref = useRef(null);
  const close = useRef(onClose);
  close.current = onClose;

  useEffect(() => {
    if (!open) return undefined;
    const opener = document.activeElement;
    const box = ref.current;
    const first = (initial && box.querySelector(initial)) || box.querySelector(FOCUSABLE) || box;
    first.focus();
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const onKeyDown = (e) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        close.current?.();
      } else if (e.key === "Tab") {
        const items = [...box.querySelectorAll(FOCUSABLE)];
        if (!items.length) return e.preventDefault();
        const [head, tail] = [items[0], items[items.length - 1]];
        if (e.shiftKey && document.activeElement === head) {
          e.preventDefault();
          tail.focus();
        } else if (!e.shiftKey && document.activeElement === tail) {
          e.preventDefault();
          head.focus();
        }
      }
    };
    box.addEventListener("keydown", onKeyDown);
    return () => {
      box.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = overflow;
      if (opener && opener.focus) opener.focus();
    };
  }, [open, initial]);
  return ref;
}

/** iOS 26's sheet: a glass close button and, if there's something to
 *  commit, a filled accent check, with the title between them. */
export function Sheet({ open, onClose, title, onConfirm, confirmLabel = "Done",
                        cancelLabel = "Cancel", confirmDisabled, children }) {
  const titleId = useId();
  const ref = useModal(open, onClose, "input, select, textarea");
  if (!open) return null;
  return (
    <div className="ios-layer ios-layer--sheet">
      <div className="ios-sheet-scrim" onClick={onClose} />
      <div className="ios-sheet" role="dialog" aria-modal="true" aria-labelledby={titleId}
           tabIndex={-1} ref={ref}>
        <div className="ios-sheet__grabber" aria-hidden="true" />
        <div className="ios-sheet__bar">
          <button type="button" className="ios-glass ios-glass-btn ios-sheet__btn"
                  aria-label={cancelLabel} data-sf-symbol="xmark" onClick={onClose}>{XMARK}</button>
          <h2 className="ios-sheet__title" id={titleId}>{title}</h2>
          {onConfirm ? (
            <button type="button"
                    className="ios-glass ios-glass--prominent ios-glass-btn ios-sheet__btn"
                    aria-label={confirmLabel} data-sf-symbol="checkmark"
                    disabled={confirmDisabled} onClick={onConfirm}>{CHECKMARK}</button>
          ) : <span />}
        </div>
        {children}
      </div>
    </div>
  );
}

/** actions: [{ label, role: "cancel" | "destructive" | undefined, onPress }].
 *  Focus starts on Cancel, the safe choice; Escape is Cancel too. More
 *  than two actions, or a long label, stacks them. */
export function Alert({ open, title, message, actions, onClose }) {
  const titleId = useId();
  const messageId = useId();
  const ref = useModal(open, onClose, ".ios-alert__cancel");
  if (!open) return null;
  const stacked = actions.length > 2 || actions.some((a) => a.label.length > 14);
  return (
    <div className="ios-layer ios-layer--center">
      <div className="ios-sheet-scrim" />
      <div className={cx("ios-alert", stacked && "ios-alert--stacked")} role="alertdialog"
           aria-modal="true" aria-labelledby={titleId}
           aria-describedby={message ? messageId : undefined} tabIndex={-1} ref={ref}>
        <h2 className="ios-alert__title" id={titleId}>{title}</h2>
        {message && <p className="ios-alert__message" id={messageId}>{message}</p>}
        <div className="ios-alert__actions">
          {actions.map((a) => (
            <button key={a.label} type="button" onClick={a.onPress ?? onClose}
                    className={cx("ios-btn", a.role === "cancel" ? "ios-alert__cancel"
                      : a.role === "destructive" ? "ios-btn--destructive" : "ios-btn--filled")}>
              {a.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

/** Choices about something the person just did. Tapping outside or
 *  Escape cancels; a destructive choice is a red label, never a red fill. */
export function ActionSheet({ open, title, message, actions, onClose }) {
  const titleId = useId();
  const ref = useModal(open, onClose);
  if (!open) return null;
  return (
    <div className="ios-layer ios-layer--bottom">
      <div className="ios-sheet-scrim" onClick={onClose} />
      <div className="ios-actionsheet" role="dialog" aria-modal="true"
           aria-labelledby={title ? titleId : undefined} tabIndex={-1} ref={ref}>
        {title && <h2 className="ios-actionsheet__title" id={titleId}>{title}</h2>}
        {message && <p className="ios-actionsheet__message">{message}</p>}
        <div className="ios-actionsheet__actions">
          {actions.map((a) => (
            <button key={a.label} type="button" onClick={a.onPress ?? onClose}
                    className={cx("ios-btn", a.role === "destructive" && "ios-btn--destructive")}>
              {a.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// For a custom surface that should behave like the kit's modals.
export { useModal };
