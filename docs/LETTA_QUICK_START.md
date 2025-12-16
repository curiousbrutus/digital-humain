# Quick Start: Letta-Style GUI

## Launch in 3 Steps

### 1. Install Dependencies (if not already done)
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment (Optional)
```bash
# If using OpenRouter instead of Ollama
echo OPENROUTER_API_KEY=sk-or-v1-xxxxx > .env
```

### 3. Launch GUI
```bash
python gui_letta.py
```

The window should open with three panels:
- **Left**: Agent settings (LLM config, agent type, system instructions)
- **Center**: Conversation simulator with tabs (Simulator, Logs, Memory)
- **Right**: Context window (token counter, core memory, archival memory)

## Your First Conversation

### Step 1: Configure Core Memory (Right Panel)

Click **"Core Memory (2)"** tab in right panel.

#### Update Human Block:
```
This is my section devoted to information about the human.
Name: [Your Name]
Role: [Your Role - e.g., Medical Staff]
Uses: Bizmed for patient records
Timezone: [Your Timezone]
Preferences: Prefers concise responses
```

Click **💾 Save** button under Human block.

#### Update Persona Block:
```
I am a Desktop Automation AI Agent specialized in medical workflows.
I help automate tasks in Bizmed (HBYS) and other desktop applications.
I'm curious, empathetic, and extraordinarily perceptive.
I understand screen contents using vision.
I can learn from demonstrations and remember important information.
I always confirm before performing destructive actions.
```

Click **💾 Save** button under Persona block.

### Step 2: Start a Conversation (Center Panel)

In the **Agent Simulator** tab:

1. Type a message in the input box:
   ```
   Hi! Can you help me open Bizmed and create a new patient record?
   ```

2. Click **▶ Send** button

3. Watch the conversation appear:
   - 👤 **USER** (blue): Your message with timestamp
   - 🤖 **AGENT** (green): Agent's response
   - 💭 **Reasoning** (italic): Agent's thought process

### Step 3: Monitor Token Usage (Right Panel)

Watch the token counter at the top of right panel:
- **Display**: "243/8192 TOKENS"
- **Progress Bar**: Green (safe), Orange (warning), Red (approaching limit)

## Common Tasks

### Record a Demonstration

1. Go to **Memory Management** tab (center panel)
2. Enter a name: `bizmed_patient_workflow`
3. Click **⏺ Start Recording**
4. Perform actions on screen (clicks, typing, etc.)
5. Click **⏹ Stop Recording**
6. Demo is saved automatically

### Replay a Demonstration

1. Select demo from dropdown: `bizmed_patient_workflow`
2. Adjust speed slider (0.5x - 2x)
3. Click **▶ Replay**
4. Watch automation execute

### Add to Archival Memory

1. Click **"Archival Memory (N)"** tab (right panel)
2. Click **+ Add** button
3. Enter content:
   ```
   Bizmed patient workflow steps:
   1. Click "New Patient" button
   2. Fill in TC Kimlik No
   3. Enter name and surname
   4. Select gender and birth date
   5. Click "Save" button
   ```
4. Click **Save**

### Search Archival Memory

1. In Archival Memory tab, enter search term: `patient`
2. Click **🔍 Search**
3. Results appear in list below
4. Click a result to view full content

## Tips for Best Results

### Memory Management
- ✅ **Update Human block** when user context changes
- ✅ **Archive important learnings** after successful tasks
- ✅ **Search archival** before asking agent to do similar tasks
- ✅ **Monitor token count** - archive and clear when near limit

### Conversation Flow
- ✅ **Be specific** in requests (mention app names, actions)
- ✅ **Review reasoning** to understand agent's approach
- ✅ **Use voice input** for hands-free operation (🎤 button)
- ✅ **Enable auto-advance** for continuous conversation

### Demonstrations
- ✅ **Record common workflows** for instant replay
- ✅ **Name demos descriptively** (e.g., `bizmed_new_patient`)
- ✅ **Test with dry run** before actual replay
- ✅ **Adjust speed** based on app responsiveness

## Keyboard Shortcuts

- **Ctrl+Enter** (in input): Send message
- **Ctrl+L**: Clear conversation
- **Ctrl+R**: Refresh models
- **Ctrl+S** (in memory blocks): Save changes

## Troubleshooting

### "Provider Health: Unhealthy"
**Problem**: Red dot next to provider selector
**Solution**: 
- Check if Ollama is running: `ollama list`
- Or set OpenRouter API key in .env file
- Click "Refresh" button

### "Token limit exceeded"
**Problem**: Token count reaches max (red progress bar)
**Solution**:
- Archive important context to Archival Memory
- Click "🗑 Clear" to reset conversation
- Core memory persists across clears

### "Character limit exceeded" (Red counter)
**Problem**: Core memory block shows red counter
**Solution**:
- Edit content to reduce length
- Move detailed info to Archival Memory
- Summarize redundant information

### Window doesn't open
**Problem**: GUI fails to launch
**Solution**:
```bash
# Check dependencies
pip install tkinter  # May need system package on Linux

# Check logs
python gui_letta.py 2>&1 | tee launch.log

# Fallback to standard GUI
python gui_main.py
```

## Example Workflows

### Medical Workflow (Bizmed)
```
1. User: "Open Bizmed and show me today's patient list"
   → Agent: Locates and launches Bizmed
   → Agent: Navigates to patient list
   → Agent: Captures and describes list

2. User: "Create a new patient record for TC: 12345678901"
   → Agent: Clicks "New Patient"
   → Agent: Enters TC number
   → Agent: Shows form ready for data entry

3. Archive: "Bizmed workflow: Open → Patient List → New Patient"
```

### Office Automation
```
1. User: "Open Excel and create a monthly report template"
   → Agent: Launches Excel
   → Agent: Creates new workbook
   → Agent: Sets up template structure

2. Record demo: "excel_monthly_report_template"
   → Can replay anytime

3. Archive: "Excel report template has columns: Date, Task, Hours, Notes"
```

## Next Steps

### Learn More
- [Complete Letta GUI Guide](LETTA_GUI.md)
- [Feature Comparison](GUI_COMPARISON.md)
- [Implementation Details](LETTA_IMPLEMENTATION_SUMMARY.md)

### Advanced Features
- Configure system instructions (left panel)
- Enable visual indicators for action feedback
- Adjust agent frequency for faster/slower responses
- Use episodic memory for automatic learning

### Share Feedback
- Found a bug? Check logs in Execution Logs tab
- Feature request? Document in archival memory
- Success story? Archive your workflow!

---

**Welcome to Digital Humain with Letta-Style Memory!** 🎉

Your agent now has:
- 🧠 Persistent memory about you (Human block)
- 🤖 Customizable personality (Persona block)
- 📚 Long-term knowledge storage (Archival memory)
- 📊 Context awareness (Token tracking)

Happy automating! 🚀
