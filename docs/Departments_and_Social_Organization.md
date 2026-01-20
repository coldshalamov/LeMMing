# Departments and Social Organization

LeMMing implements the concept of "organization of terminals" where agents are organized into departments that work together to achieve emergent intelligence through social organization.

## What is a Department?

A **department** is a logical grouping of agents that work together towards a common goal. Departments enable:

- **Modularity**: Groups of agents can be packaged and shared as a unit
- **Organization**: Large organizations can be structured into departments for clarity
- **Emergence**: Complex behaviors emerge from the interactions between departments

## Department Metadata

Each department has a `department.json` file in the `departments/` directory:

```json
{
  "name": "marketing",
  "description": "Handles marketing campaigns and content creation",
  "version": "1.0.0",
  "created_at": "2025-01-19T10:00:00Z",
  "author": "Organization Name",
  "contact": "contact@example.com",
  "dependencies": ["research", "content"],
  "tags": ["marketing", "campaigns", "content"],
  "readme": "# Marketing Department\n\nThis department handles..."
}
```

## Managing Departments

### List All Departments

```bash
python -m lemming.cli department-list
```

### Create a New Department

```bash
python -m lemming.cli department-create marketing \
  --description "Handles marketing campaigns" \
  --author "Your Name"
```

### Show Department Details

```bash
python -m lemming.cli department-show marketing
```

### Export Organization Structure

```bash
python -m lemming.cli department-export --output org-export.json
```

This creates a complete snapshot of your organization including:
- All departments
- All agents with their configurations
- The social graph (agent relationships)

### Analyze Social Graph

```bash
python -m lemming.cli department-analyze --output social-graph.json
```

This analyzes the social relationships between agents based on:
- Permission-based relationships (who can read whose outbox)
- Interaction history (actual message exchanges)
- Relationship strength based on interaction frequency

## Social Organization

### Social Relationships

LeMMing tracks social relationships between agents:

- **informed_by**: Agent A can read Agent B's outbox
- **collaborates_with**: Agents that frequently interact
- **reports_to**: Hierarchical relationships (when explicitly defined)
- **mentors**: Knowledge transfer relationships

### Relationship Strength

Each relationship has a strength value (0.0 to 1.0):
- Base strength from permissions: 0.7-0.8
- Increases with interaction frequency
- Decreases over time if no recent interactions

### Emergent Intelligence

Emergent intelligence emerges from the social organization through:

1. **Information Flow**: Messages flow through the social graph
2. **Specialization**: Different departments have different capabilities
3. **Coordination**: Agents coordinate via outbox messages
4. **Learning**: Agents build knowledge through interactions
5. **Adaptation**: Social structure evolves based on effectiveness

### Example: Marketing Department

A marketing department might consist of:

```
marketing/
├── planner/           # Plans campaigns
├── researcher/         # Researches trends
├── writer/            # Creates content
└── reviewer/          # Reviews and approves

Relationships:
planner -> researcher (informed_by)
planner -> writer (informed_by)
researcher -> writer (informed_by)
writer -> reviewer (informed_by)
reviewer -> planner (informed_by)
```

This creates a feedback loop where:
1. Planner initiates campaigns
2. Researcher provides insights
3. Writer creates content
4. Reviewer approves
5. Reviewer informs planner for next cycle

## Department Templates

Departments can be packaged as templates for easy sharing:

### Creating a Department Template

1. Create department.json in `departments/`
2. Place agent folders in `agents/`
3. All agents in the department should reference each other in `read_outboxes`

### Sharing Departments

The department structure is designed to be copy-paste friendly:

```bash
# Package a department
python -m lemming.cli department-package marketing

# This creates: departments/marketing.zip
# Unzip in another LeMMing instance to import
```

### Importing Departments

```bash
# Import a department bundle
python -m lemming.cli department-import marketing.zip --merge
```

## File System First

All department information is stored as files:

```
lemming-org/
├── departments/              # Department metadata
│   ├── marketing.json       # Marketing department definition
│   └── research.json       # Research department definition
├── social/                 # Social graph analysis
│   ├── social_graph.json   # Current social relationships
│   └── organization.json   # Complete org structure export
└── agents/                 # Agent folders
    ├── planner/
    ├── researcher/
    └── writer/
```

This ensures:
- **Transparency**: Everything is visible in the filesystem
- **Version Control**: Changes can be tracked with git
- **Portability**: Copy a folder to move a department
- **Auditability**: History of social structure evolution

## Department Design Principles

### 1. Clear Responsibility

Each department should have a clear, single responsibility:
- Marketing: Promote and engage
- Research: Gather and analyze
- Development: Build and maintain
- Operations: Run and support

### 2. Minimal Dependencies

Departments should depend on as few other departments as possible:
- Reduces coupling
- Makes sharing easier
- Improves reliability

### 3. Self-Contained

Departments should be self-contained:
- Include all necessary agents
- Define internal relationships
- Document external dependencies

### 4. Clear Interfaces

Departments should have clear interfaces:
- Well-defined message formats
- Documented outbox schemas
- Clear tool permissions

## Example Department: Content Team

```json
{
  "name": "content_team",
  "description": "Creates and manages content",
  "version": "1.0.0",
  "author": "Content Team",
  "tags": ["content", "writing", "editing"],
  "readme": "This department manages content creation workflow"
}
```

Agents:
- **content_planner**: Plans content calendar
- **content_writer**: Writes articles and posts
- **content_editor**: Reviews and edits content
- **content_publisher**: Publishes approved content

Relationships:
- content_planner reads: human
- content_writer reads: content_planner, research
- content_editor reads: content_writer
- content_publisher reads: content_editor

This creates a linear flow with feedback loops at each stage.

## Advanced: Cross-Department Collaboration

Departments can collaborate through agents that bridge them:

```
Research Department:
  ├── market_researcher
  └── tech_researcher

Marketing Department:
  ├── campaign_manager (reads: market_researcher)
  └── content_writer (reads: tech_researcher)

Product Department:
  └── product_manager (reads: campaign_manager, tech_researcher)
```

This creates emergent collaboration where:
- Research provides insights to Marketing
- Marketing creates campaigns based on insights
- Product aligns with marketing and research

## Monitoring Social Health

Monitor the social health of your organization:

### Check Social Graph

```bash
python -m lemming.cli department-analyze
```

Look for:
- **High relationship strength**: Good, active collaboration
- **Low relationship strength**: May need attention
- **Isolated agents**: Consider connecting them
- **Communication bottlenecks**: Agents with many dependents

### Export Organization

```bash
python -m lemming.cli department-export
```

Review the export for:
- Balanced department sizes
- Appropriate dependencies
- Clear social structure

## Best Practices

### 1. Start Small

Begin with small departments (2-3 agents):
- Easier to understand
- Faster to iterate
- Simpler to debug

### 2. Gradual Growth

Add complexity gradually:
- Start with linear flows
- Add feedback loops
- Introduce parallelism

### 3. Monitor Interactions

Track agent interactions:
- Review outbox entries
- Check social graph strength
- Identify bottlenecks

### 4. Iterate Based on Results

Use social graph analysis to iterate:
- Strengthen productive relationships
- Weaken unproductive ones
- Restructure as needed

## Troubleshooting

### Department Not Showing

If a department doesn't appear in `department-list`:
- Check `departments/<name>.json` exists
- Validate JSON syntax
- Verify required fields (name, description)

### Agents Not in Department

If agents aren't showing in department:
- Check agent folder naming
- Verify department name in path
- Ensure agents are under `agents/<department>/`

### Social Graph Empty

If social graph shows no relationships:
- Ensure agents have `read_outboxes` permissions
- Check that agents have run at least once
- Verify outbox entries exist

## Future Enhancements

Planned features for department management:

- **Department templates marketplace**: Share and discover departments
- **Visual department editor**: GUI for designing departments
- **Auto-organization**: Suggest department structures
- **Department performance metrics**: Track department effectiveness
- **Dynamic reorganization**: Automatically adjust social structure
