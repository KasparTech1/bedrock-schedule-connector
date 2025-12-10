# Kai Labs Project Management — AI Agent Style Guide

> **Purpose**: This document provides complete styling specifications for an AI coding agent to replicate the visual design, component architecture, and UX patterns of the Kaiville Operations Suite.

---

## Table of Contents
1. [Technology Stack](#technology-stack)
2. [Design Philosophy](#design-philosophy)
3. [Color System](#color-system)
4. [Typography](#typography)
5. [Spacing & Layout](#spacing--layout)
6. [Component Architecture](#component-architecture)
7. [UI Components Reference](#ui-components-reference)
8. [Interaction Patterns](#interaction-patterns)
9. [Shadows & Borders](#shadows--borders)
10. [Icons](#icons)
11. [Dark Mode Support](#dark-mode-support)
12. [Code Patterns](#code-patterns)

---

## Technology Stack

### Core Framework
```
React 18 + TypeScript
Vite (build tool)
```

### Styling
```
Tailwind CSS v3.4
PostCSS with Autoprefixer
tailwindcss-animate (for animations)
@tailwindcss/typography (for prose content)
```

### UI Component Library
```
shadcn/ui (New York style variant)
Radix UI primitives (all components)
class-variance-authority (cva) for component variants
clsx + tailwind-merge for class management
```

### Key Dependencies
```json
{
  "lucide-react": "^0.453.0",      // Icons
  "framer-motion": "^11.13.1",     // Animations
  "recharts": "^2.15.2",           // Charts
  "react-hook-form": "^7.55.0",    // Forms
  "zod": "^3.24.2",                // Validation
  "date-fns": "^3.6.0",            // Date utilities
  "wouter": "^3.3.5",              // Routing
  "@tanstack/react-query": "^5.60.5" // Data fetching
}
```

### shadcn/ui Configuration
```json
{
  "style": "new-york",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "client/src/index.css",
    "baseColor": "neutral",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  }
}
```

---

## Design Philosophy

### Core Principles
1. **Scanability First**: Dense information with clear visual hierarchy
2. **Consistent Patterns**: Reusable components reduce cognitive load
3. **Data Clarity**: Charts, tables, metrics are heroes—UI recedes to support them
4. **Progressive Disclosure**: Complex workflows broken into digestible steps

### Inspiration Sources
- **Linear** (project management UI patterns)
- **Notion** (content hierarchy)
- **Fluent Design** (data-heavy applications)

### What NOT to Do
- No large hero images (this is a productivity tool, not marketing)
- No parallax, complex scroll effects, or distracting motion
- No staggered reveal animations on tables/grids
- Avoid over-designed, visually heavy interfaces

---

## Color System

### CSS Variables Setup
Colors use HSL format without the `hsl()` wrapper in CSS variables for alpha channel support.

### Light Mode (`:root`)
```css
:root {
  /* Core Colors */
  --background: 210 4% 98%;           /* #F9FAFB - Light gray */
  --foreground: 210 6% 12%;           /* #1F2937 - Dark text */
  --border: 210 5% 88%;               /* #E5E7EB - Subtle border */
  
  /* Card & Container */
  --card: 210 4% 96%;                 /* #F5F6F7 - Card background */
  --card-foreground: 210 6% 14%;      /* #252A31 - Card text */
  --card-border: 210 5% 90%;          /* #E8EAEC */
  
  /* Sidebar */
  --sidebar: 210 4% 94%;              /* #F0F1F2 */
  --sidebar-foreground: 210 6% 16%;   /* #2A2F36 */
  --sidebar-border: 210 5% 86%;       /* #DCDEE0 */
  --sidebar-primary: 211 92% 42%;     /* #0C6FD9 - Blue accent */
  --sidebar-primary-foreground: 210 100% 98%;
  --sidebar-accent: 210 6% 88%;       /* #DDDFE1 */
  --sidebar-accent-foreground: 210 8% 24%;
  --sidebar-ring: 211 92% 42%;
  
  /* Popover */
  --popover: 210 5% 92%;              /* #E8E9EB */
  --popover-foreground: 210 6% 16%;
  --popover-border: 210 5% 84%;
  
  /* Primary (Blue) */
  --primary: 211 92% 42%;             /* #0C6FD9 - Main brand blue */
  --primary-foreground: 210 100% 98%; /* White text on primary */
  
  /* Secondary */
  --secondary: 210 6% 88%;            /* #DDDFE1 */
  --secondary-foreground: 210 8% 24%; /* #3A3F46 */
  
  /* Muted */
  --muted: 210 8% 90%;                /* #E2E4E6 */
  --muted-foreground: 210 7% 38%;     /* #5C6269 */
  
  /* Accent */
  --accent: 210 12% 89%;              /* #DFE2E6 */
  --accent-foreground: 210 10% 26%;   /* #3F4750 */
  
  /* Semantic Colors */
  --destructive: 0 84% 48%;           /* #DC2626 - Red */
  --destructive-foreground: 0 0% 100%;
  --warning: 38 92% 50%;              /* #F59E0B - Amber */
  --warning-foreground: 0 0% 100%;
  --success: 142 76% 36%;             /* #16A34A - Green */
  --success-foreground: 0 0% 100%;
  
  /* Form Inputs */
  --input: 210 8% 72%;                /* #B0B5BA */
  --ring: 211 92% 42%;                /* Focus ring - same as primary */
  
  /* Chart Colors */
  --chart-1: 211 92% 42%;             /* Blue */
  --chart-2: 180 84% 38%;             /* Teal */
  --chart-3: 280 76% 46%;             /* Purple */
  --chart-4: 32 92% 52%;              /* Orange */
  --chart-5: 152 68% 42%;             /* Green */
  
  /* Interaction Overlays */
  --button-outline: rgba(0,0,0, .10);
  --badge-outline: rgba(0,0,0, .05);
  --elevate-1: rgba(0,0,0, .03);      /* Hover state overlay */
  --elevate-2: rgba(0,0,0, .08);      /* Active state overlay */
  
  /* Border intensity for colored buttons */
  --opaque-button-border-intensity: -8;
}
```

### Dark Mode (`.dark`)
```css
.dark {
  /* Core Colors */
  --background: 210 6% 8%;            /* #121416 - Dark background */
  --foreground: 210 5% 92%;           /* #EAEBEC - Light text */
  --border: 210 6% 18%;               /* #292D31 */
  
  /* Card & Container */
  --card: 210 6% 11%;                 /* #1A1D1F */
  --card-foreground: 210 5% 90%;      /* #E5E6E8 */
  --card-border: 210 6% 20%;          /* #2F3337 */
  
  /* Sidebar */
  --sidebar: 210 6% 13%;              /* #1F2224 */
  --sidebar-foreground: 210 5% 88%;   /* #DDDFE1 */
  --sidebar-border: 210 6% 22%;       /* #353A3E */
  --sidebar-primary: 211 88% 48%;     /* #1E7EE3 - Brighter blue */
  --sidebar-primary-foreground: 210 100% 98%;
  --sidebar-accent: 210 8% 20%;       /* #2F3438 */
  --sidebar-accent-foreground: 210 6% 82%;
  --sidebar-ring: 211 88% 48%;
  
  /* Popover */
  --popover: 210 6% 15%;              /* #242729 */
  --popover-foreground: 210 5% 86%;
  --popover-border: 210 6% 24%;
  
  /* Primary (Blue) */
  --primary: 211 88% 48%;             /* #1E7EE3 */
  --primary-foreground: 210 100% 98%;
  
  /* Secondary */
  --secondary: 210 8% 20%;            /* #2F3438 */
  --secondary-foreground: 210 6% 82%; /* #CED0D3 */
  
  /* Muted */
  --muted: 210 10% 18%;               /* #292E32 */
  --muted-foreground: 210 8% 68%;     /* #A5AAAF */
  
  /* Accent */
  --accent: 210 14% 17%;              /* #262C31 */
  --accent-foreground: 210 8% 78%;    /* #C2C5C9 */
  
  /* Semantic Colors */
  --destructive: 0 78% 52%;           /* #E34444 */
  --destructive-foreground: 0 0% 100%;
  --warning: 38 88% 58%;              /* #F5A623 */
  --warning-foreground: 0 0% 100%;
  --success: 142 70% 45%;             /* #22B84A */
  --success-foreground: 0 0% 100%;
  
  /* Form Inputs */
  --input: 210 10% 32%;               /* #4A5057 */
  --ring: 211 88% 48%;
  
  /* Chart Colors (brightened for dark mode) */
  --chart-1: 211 88% 58%;
  --chart-2: 180 78% 52%;
  --chart-3: 280 70% 62%;
  --chart-4: 32 88% 62%;
  --chart-5: 152 62% 56%;
  
  /* Interaction Overlays */
  --button-outline: rgba(255,255,255, .10);
  --badge-outline: rgba(255,255,255, .05);
  --elevate-1: rgba(255,255,255, .04);
  --elevate-2: rgba(255,255,255, .09);
  
  /* Border intensity for colored buttons */
  --opaque-button-border-intensity: 9;
}
```

### Status Colors (Semantic)
```css
/* Status indicators - use directly, not as CSS variables */
.status-online  { color: rgb(34 197 94);  }  /* Green */
.status-away    { color: rgb(245 158 11); }  /* Amber */
.status-busy    { color: rgb(239 68 68);  }  /* Red */
.status-offline { color: rgb(156 163 175); } /* Gray */
```

### Status Badge Color Patterns
```typescript
const statusConfig = {
  GREEN: { 
    color: "text-green-600 dark:text-green-400", 
    bg: "bg-green-50 dark:bg-green-950/30" 
  },
  YELLOW: { 
    color: "text-yellow-600 dark:text-yellow-400", 
    bg: "bg-yellow-50 dark:bg-yellow-950/30" 
  },
  RED: { 
    color: "text-red-600 dark:text-red-400", 
    bg: "bg-red-50 dark:bg-red-950/30" 
  },
  PLANNING: { 
    color: "text-blue-600 dark:text-blue-400", 
    bg: "bg-blue-50 dark:bg-blue-950/30" 
  },
  ACTIVE: { 
    color: "text-green-600 dark:text-green-400", 
    bg: "bg-green-50 dark:bg-green-950/30" 
  },
  COMPLETE: { 
    color: "text-gray-600 dark:text-gray-400", 
    bg: "bg-gray-50 dark:bg-gray-950/30" 
  },
  PAUSED: { 
    color: "text-orange-600 dark:text-orange-400", 
    bg: "bg-orange-50 dark:bg-orange-950/30" 
  },
};
```

---

## Typography

### Font Families
```css
--font-sans: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
--font-serif: Georgia, serif;
--font-mono: "JetBrains Mono", Menlo, Monaco, "Courier New", monospace;
```

### Font Loading
Include Inter from Google Fonts:
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

### Type Scale
```
text-xs   → 0.75rem (12px), line-height: 1rem
text-sm   → 0.875rem (14px), line-height: 1.25rem
text-base → 1rem (16px), line-height: 1.5rem
text-lg   → 1.125rem (18px), line-height: 1.75rem
text-xl   → 1.25rem (20px), line-height: 1.75rem
text-2xl  → 1.5rem (24px), line-height: 2rem
text-3xl  → 1.875rem (30px), line-height: 2.25rem
text-4xl  → 2.25rem (36px), line-height: 2.5rem
```

### Typography Hierarchy
| Use Case | Classes |
|----------|---------|
| Display (Dashboard Headers) | `text-4xl font-bold` |
| H1 (Page Titles) | `text-3xl font-semibold` |
| H2 (Section Headers) | `text-2xl font-semibold` |
| H3 (Card/Module Titles) | `text-xl font-medium` |
| H4 (Subsections) | `text-lg font-medium` |
| Body | `text-base` (weight 400) |
| Small/Meta | `text-sm` (labels, timestamps) |
| Micro | `text-xs` (badges, counts) |
| Table Headers | `text-sm font-semibold uppercase tracking-wide` |
| Metric Values | `text-3xl font-bold` or `text-4xl font-bold` |

### Body Text
```css
body {
  @apply font-sans antialiased bg-background text-foreground;
}
```

---

## Spacing & Layout

### Spacing Scale
Use Tailwind units: `2, 3, 4, 6, 8, 12, 16, 20, 24`

### Component Spacing Patterns
```
Base spacing unit: --spacing: 0.25rem (4px)

Component internal padding: p-4 or p-6
Card spacing: p-6 (desktop), p-4 (mobile)
Section vertical rhythm: space-y-6 or space-y-8
Grid gaps: gap-4 (tight), gap-6 (standard), gap-8 (loose)
Page padding: px-6 md:px-8 lg:px-12
Stack spacing within cards: space-y-3 or space-y-4
```

### Grid Patterns
```
Dashboard metrics:    grid-cols-1 md:grid-cols-2 lg:grid-cols-4
Project cards:        grid-cols-1 md:grid-cols-2 lg:grid-cols-3
Data-heavy sections:  Single column with max-w-7xl
Two-column forms:     grid-cols-1 lg:grid-cols-2 gap-6
Health grid:          grid-cols-1 md:grid-cols-2 xl:grid-cols-3
```

### Container Strategy
```
Full-width app shell with sidebar navigation
Content areas: max-w-7xl mx-auto
Modals: max-w-lg (small), max-w-2xl (standard), max-w-4xl (wide), max-w-6xl (extra-wide for tables)
```

### Border Radius
```css
--radius: .5rem;                    /* 8px - default */
border-radius-lg: .5625rem;         /* 9px */
border-radius-md: .375rem;          /* 6px */
border-radius-sm: .1875rem;         /* 3px */
```

### Sidebar Dimensions
```css
--sidebar-width: 16rem;             /* 256px */
--sidebar-width-mobile: 18rem;      /* 288px */
--sidebar-width-icon: 3rem;         /* 48px collapsed */
```

---

## Component Architecture

### Utility Function
```typescript
// lib/utils.ts
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

### Component Variant Pattern (using CVA)
```typescript
import { cva, type VariantProps } from "class-variance-authority"

const buttonVariants = cva(
  "base-classes-here",
  {
    variants: {
      variant: {
        default: "variant-specific-classes",
        destructive: "...",
        outline: "...",
      },
      size: {
        default: "min-h-9 px-4 py-2",
        sm: "min-h-8 rounded-md px-3 text-xs",
        lg: "min-h-10 rounded-md px-8",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)
```

### File Structure
```
client/src/
├── components/
│   ├── ui/              # shadcn/ui primitives
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   └── ... (47 components)
│   ├── AppSidebar.tsx   # Main navigation
│   ├── MetricCard.tsx   # Dashboard metrics
│   ├── StatusBadge.tsx  # Status indicators
│   └── ...
├── hooks/
│   ├── use-mobile.tsx
│   ├── use-toast.ts
│   └── useAuth.ts
├── lib/
│   ├── utils.ts
│   └── queryClient.ts
├── pages/
│   └── ... (60 page components)
└── index.css            # Global styles & CSS variables
```

---

## UI Components Reference

### Button
```typescript
// Variants: default, destructive, outline, secondary, ghost
// Sizes: default (min-h-9), sm (min-h-8), lg (min-h-10), icon (h-9 w-9)

<Button variant="default">Primary Action</Button>
<Button variant="outline">Secondary</Button>
<Button variant="ghost" size="icon"><Icon /></Button>
```

**Key Classes:**
```
Base: inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md 
      text-sm font-medium focus-visible:outline-none focus-visible:ring-1 
      focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50
      [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0
      hover-elevate active-elevate-2

default:     bg-primary text-primary-foreground border border-primary-border
destructive: bg-destructive text-destructive-foreground border border-destructive-border
outline:     border [border-color:var(--button-outline)] shadow-xs active:shadow-none
secondary:   border bg-secondary text-secondary-foreground border-secondary-border
ghost:       border border-transparent
```

### Card
```typescript
<Card className="p-6">
  <CardHeader>
    <CardTitle>Title</CardTitle>
    <CardDescription>Description text</CardDescription>
  </CardHeader>
  <CardContent>Content here</CardContent>
  <CardFooter>Actions</CardFooter>
</Card>
```

**Key Classes:**
```
Card:        rounded-xl border bg-card border-card-border text-card-foreground shadow-sm
CardHeader:  flex flex-col space-y-1.5 p-6
CardTitle:   text-2xl font-semibold leading-none tracking-tight
CardDescription: text-sm text-muted-foreground
CardContent: p-6 pt-0
CardFooter:  flex items-center p-6 pt-0
```

### Badge
```typescript
// Variants: default, secondary, destructive, outline

<Badge>Default</Badge>
<Badge variant="secondary">Secondary</Badge>
<Badge variant="outline">Outlined</Badge>
```

**Key Classes:**
```
Base: whitespace-nowrap inline-flex items-center rounded-md border px-2.5 py-0.5 
      text-xs font-semibold transition-colors focus:outline-none focus:ring-2 
      focus:ring-ring focus:ring-offset-2 hover-elevate

default:     border-transparent bg-primary text-primary-foreground shadow-xs
secondary:   border-transparent bg-secondary text-secondary-foreground
destructive: border-transparent bg-destructive text-destructive-foreground shadow-xs
outline:     border [border-color:var(--badge-outline)] shadow-xs
```

### Input
```typescript
<Input type="text" placeholder="Enter value..." />
```

**Key Classes:**
```
flex h-9 w-full rounded-md border border-input bg-background px-3 py-2 
text-base ring-offset-background file:border-0 file:bg-transparent 
file:text-sm file:font-medium file:text-foreground 
placeholder:text-muted-foreground focus-visible:outline-none 
focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 
disabled:cursor-not-allowed disabled:opacity-50 md:text-sm
```

### Dialog/Modal
```typescript
<Dialog>
  <DialogTrigger asChild>
    <Button>Open</Button>
  </DialogTrigger>
  <DialogContent className="max-w-2xl">
    <DialogHeader>
      <DialogTitle>Modal Title</DialogTitle>
      <DialogDescription>Supporting text</DialogDescription>
    </DialogHeader>
    {/* Content */}
    <DialogFooter>
      <Button variant="outline">Cancel</Button>
      <Button>Confirm</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

**Key Classes:**
```
Overlay: fixed inset-0 z-50 bg-black/80 
         data-[state=open]:animate-in data-[state=closed]:animate-out 
         data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0

Content: fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg 
         translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background 
         p-6 shadow-lg duration-200 sm:rounded-lg
         data-[state=open]:animate-in data-[state=closed]:animate-out
         data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95

Header:  flex flex-col space-y-1.5 text-center sm:text-left
Title:   text-lg font-semibold leading-none tracking-tight
Footer:  flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2
```

### Table
```typescript
<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Column</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    <TableRow>
      <TableCell>Data</TableCell>
    </TableRow>
  </TableBody>
</Table>
```

**Key Classes:**
```
Table:       w-full caption-bottom text-sm
TableHeader: [&_tr]:border-b
TableBody:   [&_tr:last-child]:border-0
TableRow:    border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted
TableHead:   h-12 px-4 text-left align-middle font-medium text-muted-foreground
TableCell:   p-4 align-middle
```

### Metric Card (Custom)
```typescript
<MetricCard 
  label="Total Projects"
  value={42}
  change={12}
  trend="up"
  icon={<BarChart3 className="w-6 h-6" />}
  clickable
  onClick={() => {}}
/>
```

**Structure:**
```typescript
<Card className="p-6 hover-elevate cursor-pointer active-elevate-2">
  <div className="flex items-start justify-between">
    <div className="space-y-2">
      <p className="text-sm font-medium text-muted-foreground">{label}</p>
      <p className="text-4xl font-bold text-foreground">{value}</p>
      {change && (
        <div className="flex items-center gap-1 text-sm">
          <TrendingUp className="w-4 h-4 text-green-600" />
          <span className="text-green-600">+{change}%</span>
          <span className="text-muted-foreground">vs last month</span>
        </div>
      )}
    </div>
    <div className="text-primary opacity-60">{icon}</div>
  </div>
</Card>
```

### Status Badge (Custom)
```typescript
<StatusBadge status="GREEN" size="default" />
```

**Structure:**
```typescript
<Badge
  variant="secondary"
  className={`${config.bg} ${config.color} border-0 px-3 py-1`}
>
  <Circle className="w-2.5 h-2.5 mr-1.5 fill-current" />
  {config.label}
</Badge>
```

---

## Interaction Patterns

### Elevation System
The codebase uses a custom "elevate" system for hover/active states that overlays a semi-transparent layer.

```css
/* Hover elevation - adds subtle darkening overlay */
.hover-elevate:hover::after {
  background-color: var(--elevate-1);  /* rgba(0,0,0, .03) light / rgba(255,255,255, .04) dark */
}

/* Active elevation - stronger overlay */
.active-elevate-2:active::after {
  background-color: var(--elevate-2);  /* rgba(0,0,0, .08) light / rgba(255,255,255, .09) dark */
}

/* Toggle elevation for selected states */
.toggle-elevate.toggle-elevated::before {
  background-color: var(--elevate-2);
}
```

**Usage:**
```typescript
// Add to interactive elements
<Card className="hover-elevate">               // Subtle hover
<Card className="hover-elevate active-elevate-2"> // Hover + stronger active
<Button className="hover-elevate active-elevate-2">
```

### Focus States
```
focus-visible:outline-none 
focus-visible:ring-2 
focus-visible:ring-ring 
focus-visible:ring-offset-2
```

### Disabled States
```
disabled:pointer-events-none 
disabled:opacity-50 
disabled:cursor-not-allowed
```

### Animation Timing
```
Page transitions:    150ms fade
Modal appearance:    200ms scale + fade
Hover states:        Instant (no delay)
Loading:             Skeleton pulse animation
Data updates:        500ms highlight flash
```

### Animations (Tailwind)
```css
/* Accordion animations */
@keyframes accordion-down {
  from { height: 0 }
  to { height: var(--radix-accordion-content-height) }
}
@keyframes accordion-up {
  from { height: var(--radix-accordion-content-height) }
  to { height: 0 }
}

animation-accordion-down: accordion-down 0.2s ease-out
animation-accordion-up: accordion-up 0.2s ease-out
```

---

## Shadows & Borders

### Shadow Scale
```css
--shadow-2xs: 0px 1px 2px 0px hsl(210 10% 10% / 0.03);
--shadow-xs:  0px 1px 2px 0px hsl(210 10% 10% / 0.04);
--shadow-sm:  0px 1px 3px 0px hsl(210 10% 10% / 0.06), 
              0px 1px 2px -1px hsl(210 10% 10% / 0.04);
--shadow:     0px 2px 4px 0px hsl(210 10% 10% / 0.06), 
              0px 1px 2px -1px hsl(210 10% 10% / 0.04);
--shadow-md:  0px 4px 6px 0px hsl(210 10% 10% / 0.07), 
              0px 2px 4px -1px hsl(210 10% 10% / 0.05);
--shadow-lg:  0px 8px 12px 0px hsl(210 10% 10% / 0.08), 
              0px 4px 6px -2px hsl(210 10% 10% / 0.06);
--shadow-xl:  0px 12px 20px 0px hsl(210 10% 10% / 0.10), 
              0px 8px 10px -2px hsl(210 10% 10% / 0.07);
--shadow-2xl: 0px 20px 32px 0px hsl(210 10% 10% / 0.12);
```

### Dark Mode Shadows (Stronger)
```css
.dark {
  --shadow-2xs: 0px 1px 2px 0px hsl(210 10% 0% / 0.20);
  --shadow-xs:  0px 1px 2px 0px hsl(210 10% 0% / 0.25);
  --shadow-sm:  0px 1px 3px 0px hsl(210 10% 0% / 0.30), 
                0px 1px 2px -1px hsl(210 10% 0% / 0.20);
  /* ... etc - opacity values are 4-5x stronger in dark mode */
}
```

### Border Patterns
```
Default border:     border border-border
Card border:        border border-card-border
Subtle button:      border [border-color:var(--button-outline)]
Primary button:     border border-primary-border (auto-computed darker shade)
```

---

## Icons

### Library
Use **Lucide React** (`lucide-react`) exclusively.

### Import Pattern
```typescript
import { 
  Home, 
  Settings, 
  Users, 
  BarChart3,
  TrendingUp,
  TrendingDown,
  Circle,
  // ... import only what you need
} from "lucide-react";
```

### Standard Sizes
```
Button icons:    [&_svg]:size-4 (16px)
Sidebar icons:   [&>svg]:size-4 (16px)
Card icons:      w-6 h-6 (24px)
Status dots:     w-2.5 h-2.5 (10px)
External link:   w-3 h-3 (12px)
```

### Icon in Button
```typescript
<Button>
  <Settings className="w-4 h-4 mr-2" />
  Settings
</Button>
```

---

## Dark Mode Support

### Implementation
Uses `next-themes` with class-based toggling.

```typescript
import { ThemeProvider } from "next-themes"

<ThemeProvider attribute="class" defaultTheme="system">
  <App />
</ThemeProvider>
```

### Tailwind Config
```typescript
// tailwind.config.ts
export default {
  darkMode: ["class"],
  // ...
}
```

### Usage Pattern
Always provide dark mode variants for semantic colors:
```typescript
className="bg-green-50 dark:bg-green-950/30 text-green-600 dark:text-green-400"
```

### Theme Toggle Component
```typescript
import { useTheme } from "next-themes"
import { Moon, Sun } from "lucide-react"

function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  return (
    <Button variant="ghost" size="icon" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
      <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
    </Button>
  )
}
```

---

## Code Patterns

### Component Template
```typescript
import * as React from "react"
import { cn } from "@/lib/utils"

interface ComponentProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary"
}

const Component = React.forwardRef<HTMLDivElement, ComponentProps>(
  ({ className, variant = "default", ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "base-classes",
          variant === "secondary" && "secondary-classes",
          className
        )}
        {...props}
      />
    )
  }
)
Component.displayName = "Component"

export { Component }
```

### Page Layout Template
```typescript
export default function PageName() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Page Title</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Description text here
          </p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          Add New
        </Button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard label="Metric 1" value={42} />
        {/* ... */}
      </div>

      {/* Main Content */}
      <Card>
        <CardHeader>
          <CardTitle>Section Title</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Content */}
        </CardContent>
      </Card>
    </div>
  )
}
```

### Form Pattern
```typescript
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"

const formSchema = z.object({
  name: z.string().min(1, "Required"),
  email: z.string().email("Invalid email"),
})

type FormData = z.infer<typeof formSchema>

export function MyForm() {
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: { name: "", email: "" },
  })

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit">Submit</Button>
      </form>
    </Form>
  )
}
```

### Data Fetching Pattern
```typescript
import { useQuery, useMutation } from "@tanstack/react-query"

// Query
const { data, isLoading, error } = useQuery({
  queryKey: ["/api/projects"],
  queryFn: async () => {
    const res = await fetch("/api/projects")
    if (!res.ok) throw new Error("Failed to fetch")
    return res.json()
  },
})

// Mutation
const mutation = useMutation({
  mutationFn: async (data: NewProject) => {
    const res = await fetch("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error("Failed to create")
    return res.json()
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["/api/projects"] })
  },
})
```

---

## Accessibility

### Touch Targets
- Minimum: 44×44px (`w-11 h-11`)
- Buttons use `min-h-9` (36px) with padding

### Focus Indicators
```
2px ring with offset on all interactive elements
focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2
```

### ARIA
- Use proper `aria-label` for icon-only buttons
- Include `aria-describedby` for form errors
- Use `sr-only` class for screen reader text

### Keyboard Navigation
- Cmd/Ctrl+K: Search
- Cmd/Ctrl+B: Toggle sidebar
- Esc: Close modals
- Tab: Focus navigation

---

## Quick Reference Cheat Sheet

### Common Class Combinations
```typescript
// Card with hover
"rounded-xl border bg-card border-card-border text-card-foreground shadow-sm hover-elevate"

// Section title
"text-2xl font-semibold"

// Muted helper text
"text-sm text-muted-foreground"

// Interactive card
"p-6 hover-elevate cursor-pointer active-elevate-2"

// Form label
"text-sm font-medium mb-2 block"

// Button group
"flex gap-2"

// Page section spacing
"space-y-6"

// Responsive grid
"grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"

// Full-width table container
"relative w-full overflow-auto"
```

### Color Quick Reference
| Semantic | Light Mode | Dark Mode |
|----------|------------|-----------|
| Primary | `#0C6FD9` | `#1E7EE3` |
| Background | `#F9FAFB` | `#121416` |
| Card | `#F5F6F7` | `#1A1D1F` |
| Border | `#E5E7EB` | `#292D31` |
| Muted text | `#5C6269` | `#A5AAAF` |
| Success | `#16A34A` | `#22B84A` |
| Warning | `#F59E0B` | `#F5A623` |
| Destructive | `#DC2626` | `#E34444` |

---

## File Templates

### Tailwind Config
See: `tailwind.config.ts`

### Global CSS
See: `client/src/index.css`

### Component JSON (shadcn)
See: `components.json`

---

**End of Style Guide**

*Last Updated: December 2024*
*Version: 1.0*

