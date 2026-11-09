// Every component in ios.jsx, on one screen. Also what
// scripts/eval/test_react_kit.py drives in a browser.
import { useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ActionSheet, Alert, Badge, Bars, Button, Card, Carousel, Chip, ControlButton, Controls, EmptyState,
  Field, Hero, LargeTitle, List, Metric, NavBar, PageControl, Progress, Ring, Row, SectionHeader,
  Segmented, Sheet, Slider, Stats, Stepper, Switch, TabBar, Tile, Tiles, useCollapsed,
} from "./ios.jsx";

const stroke = { fill: "none", stroke: "currentColor", strokeWidth: 2,
                 strokeLinecap: "round", strokeLinejoin: "round" };
const Icon = ({ d }) => (
  <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" {...stroke}><path d={d} /></svg>
);
const PLUS = "M12 5v14M5 12h14";
const FORK = "M7 3v8M5 3v5a2 2 0 0 0 4 0V3M7 11v10M16 3c-2 1-3 3-3 6s1 4 3 4v8";
const TRAM = "M6 3h12a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2zM4 9h16M8 21l2-4M16 21l-2-4";
const LIST = "M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01";
const GEAR = "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19 12l2-1-1-3-2 .2-1.3-1.3.2-2-3-1-1 2h-2L9 3 6 4l.2 2L5 7.3 3 7 2 10l2 1v2l-2 1 1 3 2-.2 1.3 1.3-.2 2 3 1 1-2h2l1 2 3-1-.2-2 1.3-1.3 2 .2 1-3-2-1z";
const TRAY = "M3 13h5l2 3h4l2-3h5M5 5l-2 8v5a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1v-5l-2-8z";

function App() {
  const [tab, setTab] = useState("expenses");
  const [period, setPeriod] = useState("month");
  const [nudge, setNudge] = useState(true);
  const [split, setSplit] = useState(2);
  const [budget, setBudget] = useState(60);
  const [empty, setEmpty] = useState(false);
  const [adding, setAdding] = useState(false);
  const [title, setTitle] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [sharing, setSharing] = useState(false);
  const [page, setPage] = useState(0);
  const [log, setLog] = useState([]);
  const note = (s) => setLog((l) => [...l, s]);
  const collapsed = useCollapsed();

  return (
    <main>
      <NavBar title="Expenses" collapsed={collapsed} trailing={
        <Controls>
          <ControlButton label="Add Expense" symbol="plus" onClick={() => setAdding(true)}>
            <Icon d={PLUS} />
          </ControlButton>
        </Controls>
      } />
      <LargeTitle>Expenses</LargeTitle>

      {/* Content first: the screen opens on what the person came for. */}
      <div className="ios-inset" style={{ display: "grid", gap: 12, marginBottom: 16 }}>
        <Hero eyebrow="This month" title="£412 spent" symbol="sterlingsign.circle.fill"
              glyph={<Icon d={TRAY} />} action="See Budget" onAction={() => note("budget")}
              onClick={() => note("open month")}>£88 left of £500</Hero>
        <Card title="Budget" symbol="chart.pie.fill" icon={<Icon d={TRAY} />} meta="Today" tint="orange"
              onClick={() => note("open budget")}>
          <div className="ios-card__split">
            <Metric value="82" unit="%" label="of the month's budget" />
            <Ring value={0.82} label="82% of the budget spent" tint="orange" />
          </div>
          <Progress value={0.82} label="Budget used" tint="orange" />
        </Card>
        <Tiles>
          <Tile title="Food" subtitle="This week" count={12} tint="green" symbol="fork.knife"
                icon={<Icon d={FORK} />} onClick={() => note("open food")} />
          <Tile title="Travel" subtitle="This week" count={4} tint="blue" filled symbol="tram.fill"
                icon={<Icon d={TRAM} />} onClick={() => note("open travel")} />
        </Tiles>
        <Card title="Last 7 Days" tint="teal" meta={<Badge tint="red">Over</Badge>}>
          <Bars values={[0.3, 0.5, 0.2, 0.6, 0.4, 0.7, 0.9]} labels={["M", "T", "W", "T", "F", "S", "S"]}
                label="Spending each day this week, most today" tint="teal" />
        </Card>
        <Stats items={[{ label: "Average", value: "£14" }, { label: "Largest", value: "£42" },
                       { label: "Count", value: "31" }]} />
        <SectionHeader title="Accounts" action="See All" onAction={() => note("see all accounts")} />
        <Carousel label="Accounts">
          <Hero title="Everyday" eyebrow="£1,240" tint="indigo" glyph={<Icon d={LIST} />}
                onClick={() => note("open everyday")} />
          <Hero title="Savings" eyebrow="£6,800" tint="green" glyph={<Icon d={LIST} />}
                onClick={() => note("open savings")} />
        </Carousel>
      </div>

      <div className="ios-inset">
        <Segmented label="Period" value={period} onChange={setPeriod}
                   options={[{ value: "week", label: "Week" }, { value: "month", label: "Month" }]} />
      </div>

      {empty ? (
        <EmptyState symbol="tray" icon={<Icon d={TRAY} />} title="No expenses yet"
                    action="Add Expense" onAction={() => setAdding(true)}>
          Everything you spend shows up here.
        </EmptyState>
      ) : (
        <List header="This month" footer="Totals include split bills at your share.">
          <Row title="Lunch at Kiln" value="£18.40" symbol="fork.knife" icon={<Icon d={FORK} />}
               onClick={() => note("open Lunch at Kiln")} />
          <Row title="Monthly tram pass" value="£42.00" symbol="tram.fill" icon={<Icon d={TRAM} />}
               onClick={() => setDeleting(true)} />
        </List>
      )}

      <List header="Settings">
        <Row title="Daily nudge" accessory={<Switch checked={nudge} onChange={setNudge} />} />
        <Row title="Split between" value={`${split} people`}
             accessory={<Stepper label="people" value={split} min={1} max={8} onChange={setSplit} />} />
        <Row title="Date"><span className="ios-list__value"><Chip>Jul 31, 2025</Chip></span></Row>
      </List>
      <List header="Budget used">
        <Row><Slider label="Budget used" value={budget} onChange={setBudget} /></Row>
      </List>

      <div className="ios-inset" style={{ display: "grid", gap: 8 }}>
        <Button variant="filled" wide onClick={() => setSharing(true)}>Share Report</Button>
        <Button variant="tinted" wide onClick={() => setEmpty((e) => !e)}>Toggle Empty</Button>
        <Button destructive wide onClick={() => setDeleting(true)}>Delete All</Button>
      </div>
      <div style={{ display: "flex", justifyContent: "center", padding: 16 }}>
        <PageControl count={8} index={page} onChange={setPage} />
      </div>
      <output id="log">{log.join("|")}</output>

      <Sheet open={adding} title="New Expense" onClose={() => setAdding(false)}
             confirmLabel="Add" confirmDisabled={!title}
             onConfirm={() => { note(`added ${title}`); setAdding(false); setTitle(""); }}>
        <List>
          <Row><Field placeholder="Description" aria-label="Description" value={title}
                      onChange={(e) => setTitle(e.target.value)} /></Row>
          <Row><Field placeholder="Amount" aria-label="Amount" inputMode="decimal" /></Row>
        </List>
      </Sheet>

      <Alert open={deleting} title="Delete this expense?" message="This can’t be undone."
             onClose={() => setDeleting(false)}
             actions={[{ label: "Cancel", role: "cancel" },
                       { label: "Delete", role: "destructive",
                         onPress: () => { note("deleted"); setDeleting(false); } }]} />

      <ActionSheet open={sharing} title="Share report" onClose={() => setSharing(false)}
                   actions={[{ label: "Copy Link", onPress: () => { note("copied"); setSharing(false); } },
                             { label: "Email", onPress: () => setSharing(false) }]} />

      <TabBar selected={tab} onSelect={setTab} tabs={[
        { id: "expenses", label: "Expenses", symbol: "list.bullet", icon: <Icon d={LIST} /> },
        { id: "budgets", label: "Budgets", symbol: "chart.pie", icon: <Icon d={TRAY} /> },
        { id: "settings", label: "Settings", symbol: "gear", icon: <Icon d={GEAR} /> },
      ]} />
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
