/* Taps for a design prototype, wired by attribute rather than by hand.
 *
 * A design that looks like an app and does nothing when you tap it reads
 * as a picture of an app. These five attributes cover what a reviewer
 * taps first, so no screen needs its own script for them:
 *
 *   data-go="saved"       show the screen data-screen-id="saved" in place of
 *                         its siblings, and select every control that goes
 *                         there (a tab bar, a sidebar, a nav rail)
 *   data-push="plant"     open data-screen-id="plant" on top, the way a list
 *                         row pushes a detail; data-back returns
 *   data-sheet="new"      open data-sheet-id="new"; data-dismiss inside it
 *                         closes it, and so does its scrim
 *   data-toggle           flip aria-pressed, or aria-checked on role=switch
 *   data-toast="Saved"    show a short confirmation banner
 *   data-item="plants.fig"  the record the opened screen fills from (below)
 *
 * Screens and sheets are hidden with the hidden attribute until opened.
 * A plain script, not a module: the design opens straight from a file,
 * and browsers refuse to run modules from one.
 *
 * Each row its own detail. A list pushes one detail screen, and without
 * data every row opened the same plant. Put the records in one block and
 * name a record on the control that opens the screen:
 *
 *   <script type="application/json" id="prototype-data">
 *     {"plants": {"fig": {"name": "Fiddle-leaf fig", "room": "Living room",
 *                          "tint": "var(--ios-green)",
 *                          "history": [{"date": "31 Oct", "note": "On time"}]}}}
 *   </script>
 *   <li data-push="plant" data-item="plants.fig">...</li>
 *
 * The opened screen or sheet fills itself from the record:
 *
 *   data-field="name"        the element's text
 *   data-field-src="photo"   any attribute: src, href, alt, aria-label...
 *   data-field-tint="tint"   the --tint the content parts take their colour from
 *   data-field-class="kind"  a class, replacing the one it added last time
 *   data-show="overdue"      shown only when the record's value is truthy
 *   data-each="history"      a list: its <template> is repeated per item,
 *                            and fields inside it read from that item
 *
 * A key can be a path ("care.light"). data-item can also be a record
 * written inline as JSON. Keep the screen's own markup filled with the
 * first record, so it reads right before anything is tapped and in the
 * Figma export.
 */
(function () {
  "use strict";

  var history = [];
  var DATA = null;

  function data() {
    if (DATA === null) {
      var block = document.getElementById("prototype-data");
      try { DATA = block ? JSON.parse(block.textContent) : {}; }
      catch (e) { DATA = {}; console.error("prototype-data is not valid JSON: " + e.message); }
    }
    return DATA;
  }

  function lookup(obj, path) {
    return String(path).split(".").reduce(function (o, k) {
      return o == null ? undefined : o[k];
    }, obj);
  }

  function record(el) {
    var ref = el.getAttribute("data-item");
    if (ref === null) return null;
    ref = ref.trim();
    if (ref.charAt(0) === "{") {
      try { return JSON.parse(ref); } catch (e) { console.error("data-item is not valid JSON: " + ref); return null; }
    }
    var rec = lookup(data(), ref);
    if (rec === undefined) console.error("data-item \"" + ref + "\" is not in prototype-data");
    return rec === undefined ? null : rec;
  }

  // The fields of one element, from one record.
  function fillOne(el, rec) {
    Array.prototype.forEach.call(el.attributes, function (a) {
      if (a.name.indexOf("data-field") !== 0) return;
      var value = lookup(rec, a.value);
      if (value === undefined) return;
      if (a.name === "data-field") {
        el.textContent = value;
      } else if (a.name === "data-field-tint") {
        el.style.setProperty("--tint", value);
      } else if (a.name === "data-field-class") {
        if (el._fieldClass) el.classList.remove(el._fieldClass);
        if (value) el.classList.add(value);
        el._fieldClass = value;
      } else {
        el.setAttribute(a.name.slice("data-field-".length), value);
      }
    });
    if (el.hasAttribute("data-show")) el.hidden = !lookup(rec, el.getAttribute("data-show"));
  }

  // An element and everything under it, from one record. A list
  // (data-each) stops the walk: its rows read from their own items.
  function fill(el, rec) {
    fillOne(el, rec);
    if (el.hasAttribute("data-each")) { list(el, rec); return; }
    Array.prototype.forEach.call(el.children, function (child) {
      if (child.tagName !== "TEMPLATE") fill(child, rec);
    });
  }

  function list(el, rec) {
    var items = lookup(rec, el.getAttribute("data-each"));
    var tpl = el.querySelector(":scope > template");
    if (!tpl || !Array.isArray(items)) return;
    // The rows written into the markup stand for the first record; the
    // template's copies replace them.
    Array.prototype.slice.call(el.children).forEach(function (c) {
      if (c !== tpl) c.remove();
    });
    items.forEach(function (item) {
      var frag = tpl.content.cloneNode(true);
      Array.prototype.slice.call(frag.children).forEach(function (c) { fill(c, item); });
      el.appendChild(frag);
    });
  }

  if (/[?&]review\b/.test(location.search)) document.documentElement.classList.add("review");

  function screen(id) {
    return document.querySelector('[data-screen-id="' + id + '"]');
  }

  function show(target) {
    var parent = target.parentElement;
    if (parent) {
      Array.prototype.forEach.call(parent.children, function (el) {
        if (el !== target && el.hasAttribute("data-screen-id")) el.hidden = true;
      });
    }
    target.hidden = false;
    var scroller = target.closest(".phone, .ios-body, .m3-body, .ipad-content, .mac-content");
    if (scroller) scroller.scrollTop = 0;
  }

  function current(near) {
    var parent = near.parentElement;
    if (!parent) return null;
    return Array.prototype.find.call(parent.children, function (el) {
      return el.hasAttribute("data-screen-id") && !el.hidden;
    }) || null;
  }

  function select(id) {
    document.querySelectorAll("[data-go]").forEach(function (el) {
      var on = el.getAttribute("data-go") === id;
      if (el.getAttribute("role") === "tab" || el.hasAttribute("aria-selected") ||
          el.closest('[role="tablist"], .ios-tabbar, .ipad-tabbar')) {
        el.setAttribute("aria-selected", String(on));
      } else if (on) {
        el.setAttribute("aria-current", "page");
      } else {
        el.removeAttribute("aria-current");
      }
    });
  }

  function toast(text) {
    var host = document.querySelector(".device, .ipad, .mac-window, .m3-device") || document.body;
    var el = host.querySelector(".proto-toast");
    if (!el) {
      el = document.createElement("div");
      // Each kit's own banner: Material's snackbar on Android, a glass
      // capsule elsewhere.
      el.className = host.classList.contains("m3-device")
        ? "proto-toast m3-snackbar m3-snackbar--anchored" : "proto-toast ios-glass";
      el.setAttribute("role", "status");
      if (!host.classList.contains("m3-device")) {
        el.style.cssText = "position:absolute;left:16px;right:16px;bottom:96px;z-index:60;" +
          "padding:14px 20px;border-radius:999px;text-align:center;" +
          "font:var(--ios-text-subhead, 15px/20px system-ui);color:var(--ios-label-vibrant, inherit)";
      }
      host.appendChild(el);
    }
    el.textContent = text;
    el.hidden = false;
    clearTimeout(el._timer);
    el._timer = setTimeout(function () { el.hidden = true; }, 2400);
  }

  document.addEventListener("click", function (event) {
    var el = event.target.closest("[data-go], [data-push], [data-back], [data-sheet], [data-dismiss], [data-toggle], [data-toast], [data-sheet-id]");
    if (!el) return;
    // Only a control triggers: a screen or device that happens to carry one
    // of these attributes as a flag is not something you tap.
    if (!el.hasAttribute("data-sheet-id") &&
        !el.matches("button, a, li, [role], [tabindex], .ios-list__row--tappable, .m3-list__item--tappable")) return;

    if (el.hasAttribute("data-sheet-id")) {
      // A tap on the sheet's own backdrop, not on anything inside it.
      if (event.target === el || event.target.classList.contains("ios-sheet-scrim") ||
          event.target.classList.contains("ipad-scrim") || event.target.classList.contains("m3-scrim")) {
        el.hidden = true;
      }
      return;
    }

    var id;
    if ((id = el.getAttribute("data-go")) !== null) {
      var target = screen(id);
      if (target) {
        var grec = record(el);
        if (grec) fill(target, grec);
        show(target); history = [];
      }
      select(id);
    } else if ((id = el.getAttribute("data-push")) !== null) {
      var detail = screen(id);
      if (detail) {
        var from = current(detail);
        if (from) history.push(from);
        var rec = record(el);
        if (rec) fill(detail, rec);
        show(detail);
      }
    } else if (el.hasAttribute("data-back")) {
      var back = history.pop();
      if (back) show(back);
    } else if ((id = el.getAttribute("data-sheet")) !== null) {
      var sheet = document.querySelector('[data-sheet-id="' + id + '"]');
      if (sheet) {
        var srec = record(el);
        if (srec) fill(sheet, srec);
        sheet.hidden = false;
      }
    } else if (el.hasAttribute("data-dismiss")) {
      var open = el.closest("[data-sheet-id]");
      if (open) open.hidden = true;
    }

    if (el.hasAttribute("data-toggle")) {
      var attr = el.getAttribute("role") === "switch" ? "aria-checked" : "aria-pressed";
      el.setAttribute(attr, String(el.getAttribute(attr) !== "true"));
    }
    if (el.hasAttribute("data-toast")) toast(el.getAttribute("data-toast"));
  });
})();
