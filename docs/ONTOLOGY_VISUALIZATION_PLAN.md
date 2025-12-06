# Ontology Visualization Plan

## Overview

Add an interactive visualization for the maintenance domain ontology, showing class hierarchies, properties, relationships, and constraints in the terminal-themed UI.

## Current Ontology Structure

### Classes (17 total)
- **Component Hierarchy** (12 classes):
  - Component (root)
    - RotatingComponent → Motor → ElectricMotor
    - RotatingComponent → Pump → HydraulicPump, VacuumPump
    - StaticComponent → Valve → ControlValve, ShutoffValve
    - StaticComponent → Container
    - Sensor → PressureSensor, TemperatureSensor

- **Event Hierarchy** (4 classes):
  - Event (root) → MaintenanceEvent, FailureEvent, MeasurementEvent

- **Other Classes** (2):
  - Plant, Technician

### Properties
- **Object Properties** (4): hasComponent, isPartOf, hasMaintenance, performedBy
- **Datatype Properties** (9): operatingHours, maxLifespan, maintenanceInterval, serialNumber, pressure, temperature, date, rpm, status

### Constraints (8)
- C1-C3: Range constraints (non-negative, positive values)
- C4-C5: Relational constraints (intervals vs lifespan)
- C6-C8: Physical constraints (pressure, temperature, RPM limits)

## Visualization Components

### 1. Interactive Graph View (Primary)
**Technology**: D3.js force-directed graph with terminal styling

**Features**:
- Nodes represent classes (color-coded by category)
- Edges represent subclass relationships and object properties
- Click node to see details (properties, constraints)
- Zoom/pan support
- Terminal green color scheme with glow effects

**Node Types**:
- Component classes: Bright green circles
- Event classes: Amber circles
- Other classes: Cyan circles
- Properties shown as smaller nodes or labels on edges

### 2. Tree View (Secondary)
**Features**:
- Collapsible tree structure
- Shows class hierarchy clearly
- Toggle between Component tree and Event tree
- ASCII-style connectors (├── └──) matching terminal theme

### 3. Property Panel
**Features**:
- Click a class to show its properties
- Display datatype properties with:
  - Name
  - Data type
  - Constraints/range
- Display object properties with:
  - Domain → Range
  - Inverse property (if any)

### 4. Constraint Visualization
**Features**:
- Visual representation of constraint relationships
- Highlight affected properties
- Show constraint expressions
- Color by constraint type (range=green, relational=amber, physical=cyan)

## Implementation Steps

### Step 1: Backend API Endpoint
Create `/api/ontology/graph` endpoint returning:
```json
{
  "nodes": [
    {"id": "Component", "type": "class", "category": "component", "description": "..."},
    ...
  ],
  "edges": [
    {"source": "Motor", "target": "RotatingComponent", "type": "subclass"},
    {"source": "Plant", "target": "Component", "type": "hasComponent"},
    ...
  ],
  "properties": {
    "datatype": [...],
    "object": [...]
  },
  "constraints": [...]
}
```

### Step 2: Frontend Template
Create `/visualization` route with:
- SVG container for D3.js graph
- Side panel for details
- Toggle buttons for view modes
- Legend

### Step 3: JavaScript Visualization
- D3.js force simulation
- Node drag behavior
- Click handlers for details
- Zoom/pan controls
- Terminal-themed styling

### Step 4: CSS Styling
- Glow effects on nodes/edges
- Terminal color palette
- Responsive layout
- Animation effects

## File Changes

### New Files
1. `src/logic_guard_layer/web/templates/visualization.html` - Main template
2. `src/logic_guard_layer/web/static/js/ontology-viz.js` - D3.js visualization
3. `src/logic_guard_layer/web/static/css/visualization.css` - Additional styles

### Modified Files
1. `src/logic_guard_layer/main.py` - Add API endpoint and route
2. `src/logic_guard_layer/web/templates/base.html` - Add nav link
3. `src/logic_guard_layer/ontology/loader.py` - Add method to export graph data

## UI Mockup

```
┌─────────────────────────────────────────────────────────────────┐
│ > LOGIC-GUARD-LAYER v1.0.0                                      │
│ [HOME] [VALIDATE] [HISTORY] [ONTOLOGY] [VISUALIZATION]          │
├─────────────────────────────────────────────────────────────────┤
│ > ONTOLOGY VISUALIZATION                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Graph View] [Tree View] [Constraints]     ┌─────────────────┐ │
│                                              │ SELECTED: Motor │ │
│       ┌──────────┐                          │                 │ │
│       │Component │                          │ Type: Class     │ │
│       └────┬─────┘                          │ Parent: Rotating│ │
│    ┌───────┼───────┐                        │                 │ │
│    ▼       ▼       ▼                        │ PROPERTIES:     │ │
│ ┌─────┐ ┌─────┐ ┌──────┐                    │ - rpm: 0-10000  │ │
│ │Rotat│ │Stati│ │Sensor│                    │ - hours: >= 0   │ │
│ └──┬──┘ └─────┘ └──────┘                    │ - lifespan: > 0 │ │
│    ▼                                         │                 │ │
│ ┌─────┐  ┌─────┐                            │ CONSTRAINTS:    │ │
│ │Motor│──│Pump │                            │ - C1, C2, C5    │ │
│ └─────┘  └─────┘                            │ - C8 (RPM)      │ │
│                                              └─────────────────┘ │
│                                                                 │
│ Legend: ● Component  ● Event  ● Other  ─── subclass  ··· prop  │
└─────────────────────────────────────────────────────────────────┘
```

## Timeline Estimate
- Backend API: 1 file
- Frontend template: 1 file
- D3.js visualization: 1 file
- CSS styling: 1 file
- Integration: Updates to 2-3 existing files

Total: ~6 files to create/modify
