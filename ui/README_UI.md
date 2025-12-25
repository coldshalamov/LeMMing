# LeMMing Dashboard UI

This is the official Next.js Dashboard for LeMMing.

## Features

- **Org Graph Visualization**: Real-time graph of agent permissions and communication lines.
- **Agent Inspector**: "Baseball Card" style view for each agent with stats and scheduling info.
- **Real-time Monitoring**: Visualizes ticks, messages, and credit usage.
- **Agent Wizard**: Step-by-step wizard to create new agent resumes (Simulation Mode).

## Setup

1. Ensure the LeMMing Python API is running if you want real data:

   ```bash
   python -m lemming.cli serve
   ```

   _Note: By default, the UI runs in MOCK MODE for development. To switch to real API, edit `ui/lib/api.ts` and set `USE_MOCK = false`._

2. Install dependencies (if not already done):

   ```bash
   npm install
   ```

3. Run the development server:

   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000)

## Architecture

- **Framework**: Next.js 15 (App Router)
- **Styling**: Tailwind CSS v4 (Neo-Terminal Theme)
- **Data**: SWR hooks with Mock/Real toggle.
- **Animation**: Framer Motion.
