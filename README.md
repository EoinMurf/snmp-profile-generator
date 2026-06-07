# SNMP Profile Generator

A local browser tool that reads an `snmpwalk` output file and generates a structured SNMP monitoring profile in YAML format.

Drop in a walk file, get a clean profile — no cloud, no account, no vendor lock-in.

---

## What it does

- Parses raw `snmpwalk` output (`.OID = TYPE: value` format)
- Detects the device vendor from `sysObjectID`
- Separates standard MIB-II scalars, interface/IP/entity tables, and enterprise-specific OIDs
- Resolves enterprise OID names via [mibs.observium.org](https://mibs.observium.org/) (requires the backend to be running)
- Outputs a generic YAML profile with `sysobjectid`, `scalars`, `tables`, and `device_tags`
- Optional export formatted for specific monitoring tools

---

## How to use

### 1. Install dependencies

```bash
pip install flask
```

Or with the requirements file:

```bash
pip install -r requirements.txt
```

### 2. Start the backend server

The backend is a small Flask proxy that resolves enterprise OID names against the Observium MIB database (the browser can't call it directly due to CORS).

```bash
python3 app.py
```

You should see:

```
──────────────────────────────────────────────────
  SNMP Profile Generator  →  http://localhost:7788
  MIB lookup: mibs.observium.org
──────────────────────────────────────────────────
```

### 3. Open the app

Navigate to [http://localhost:7788](http://localhost:7788) in your browser.

### 4. Load your snmpwalk file

Drag and drop your `snmpwalk` output file onto the drop zone, or click **Browse** to select it.

The walk file should be in the standard format produced by `snmpwalk`:

```
.1.3.6.1.2.1.1.1.0 = STRING: Cisco IOS Software ...
.1.3.6.1.2.1.2.2.1.10.1 = Counter32: 123456
.1.3.6.1.4.1.9.9.109.1.1.1.1.2.1 = Gauge32: 12
```

### 5. Review and download the profile

The generated YAML appears on the right. The profile includes:

- **`sysobjectid`** — the device's OID identity
- **`scalars`** — single-value OIDs (uptime, hostname, etc.)
- **`tables`** — indexed OID groups (interfaces, IP addresses, etc.) split into `metrics` and `tags`
- **`device_tags`** — descriptive system fields

Click **Download .yaml** to save the profile, or use **Export for tool ▾** to get a version formatted for a specific monitoring platform.

---

## How enterprise OID names are resolved

Standard MIB-II OIDs (`1.3.6.1.2.1.*`) are resolved from a built-in knowledge base.

For enterprise OIDs (`1.3.6.1.4.1.*`), the backend queries `mibs.observium.org` in parallel and substitutes human-readable names into the YAML. A green dot in the header means the backend is reachable and MIB lookup is active. If the server is offline, OIDs get auto-generated names like `ent_9_9_109_col_2`.

---

## Without the backend

The app works offline — it just won't resolve enterprise OID names. Standard MIB-II tables (interfaces, IP, TCP, UDP, entity, host-resources) are always resolved from the built-in knowledge base regardless of server state.

---

## Generating a walk file

If you need to produce a walk file from a live device:

```bash
snmpwalk -v2c -c <community> -O n <device-ip> .1 > device_walk.txt
```

The `-O n` flag outputs numeric OIDs, which this tool requires.
