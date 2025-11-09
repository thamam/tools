# Prompt Enhancer Pro - Chrome Extension

A Chrome extension that enhances prompts following systematic prompt engineering guidelines from your Prompt Engineering Project.

## Features

### 🎯 Interaction Modes
- **Zero Shot**: Execute immediately, no questions allowed
- **Zero Shot Relaxed**: One clarification question permitted
- **Interactive**: Step-by-step with mandatory checkpoints

### 🤖 Platform Optimization
- **Claude Optimization**: XML structure, explicit instructions
- **GPT-4 Optimization**: JSON format, structured output

### 🔧 Quick Fixes
- **Fix Anti-Patterns**: Automatically fixes vague verbs, adds output format, success criteria
- **Add Structure**: Adds comprehensive prompt structure

### 📊 Evaluation
- **Evaluate & Score**: Analyzes prompt quality across 4 dimensions (Clarity, Specificity, Completeness, Efficiency)

## Installation

### Method 1: Load Unpacked Extension (Development)

1. **Generate Icons** (one-time setup):
   ```bash
   cd prompt-enhancer-extension
   node generate-icons.js
   ```

2. **Open Chrome Extensions Page**:
   - Navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top-right)

3. **Load Extension**:
   - Click "Load unpacked"
   - Select the `prompt-enhancer-extension` directory
   - Extension should now appear in your toolbar

### Method 2: Build and Package (Production)

```bash
cd prompt-enhancer-extension
# Icons should already exist from Method 1
# Zip the entire directory
zip -r prompt-enhancer-pro.zip . -x "*.git*" -x "node_modules/*" -x "generate-icons.js"
```

Then load the .zip file in Chrome Extensions.

## Usage

1. **Select Text**: Highlight any text on a webpage that you want to enhance

2. **Right-Click**: Open the context menu

3. **Choose Enhancement**:
   ```
   Prompt Enhance →
     ├── Enforce Mode →
     │   ├── 🎯 Zero Shot (No Questions)
     │   ├── 🎯 Zero Shot Relaxed (1 Question OK)
     │   └── 💬 Interactive (Step-by-Step)
     │
     ├── Optimize for Platform →
     │   ├── 🤖 Optimize for Claude
     │   └── 🧠 Optimize for GPT-4
     │
     ├── Quick Fixes →
     │   ├── 🔧 Fix Anti-Patterns
     │   └── 📋 Add Structure & Format
     │
     └── 📊 Evaluate & Score
   ```

4. **Text Replaced**: The selected text is automatically replaced with the enhanced version

5. **Visual Feedback**: A notification appears confirming the enhancement

## Enhancement Examples

### Before: Vague Prompt
```
Analyze this data and make it better
```

### After: Zero Shot Enhancement
```
[ZERO SHOT MODE - Execute immediately, no questions]

You are not permitted to ask clarifying questions.
You must make reasonable assumptions.
Proceed with implementation immediately.

Analyze this data and make it better

DO NOT ask clarifying questions.
DO NOT suggest alternatives unless explicitly required.
PROCEED with implementation immediately.
```

### After: Fix Anti-Patterns
```
/* Enhanced Prompt - Anti-patterns Fixed */
/* Issues addressed: Replaced vague verb "analyze", Added explicit output format, Added success criteria */

Extract key metrics, identify patterns, and provide actionable insights on this data and enhance clarity and reduce length by 30% while maintaining key information in it better

Output Format:
1. [Primary result]
2. [Supporting details]
3. [Validation/verification]

Success Criteria:
- [Define what successful completion looks like]

Error Handling:
If input is unclear or incomplete, specify what information is needed before proceeding.
```

### After: Claude Optimization
```xml
<instructions>
<task>
Analyze this data and make it better
</task>

<requirements>
- Define clear success criteria
- Specify output format
- Include validation steps
</requirements>

<output_format>
<response>
  <analysis>Your analysis here</analysis>
  <implementation>Your implementation here</implementation>
  <validation>Verification steps</validation>
</response>
</output_format>

<constraints>
- Use explicit, structured instructions
- Follow XML formatting for outputs
- Include error handling
- Document assumptions
</constraints>
</instructions>
```

### After: Evaluation
```
# Prompt Evaluation Report

## Original Prompt:
Analyze this data and make it better

## Quality Assessment:

### Clarity: 2/5
- Contains vague terms: analyze, better

### Specificity: 2/5
- No output format specified
- No examples provided

### Completeness: 2/5
- No success criteria defined
- No error handling specified

### Efficiency: 3/5
✓ Concise and efficient

## Total Score: 9/20

## Recommendations:
⚠ Significant improvements recommended

## Suggested Improvements:
Replace vague verbs with specific actions
Add explicit output format
Define measurable success criteria
Include 1-2 examples of desired output
Add error handling instructions
```

## Works With

### Text Inputs
- ✅ Textareas (ChatGPT, Claude.ai, etc.)
- ✅ Input fields
- ✅ ContentEditable elements
- ✅ Code editors (CodeMirror, Monaco)
- ✅ Markdown editors
- ✅ Google Docs (limited)

### LLM Platforms Tested
- ✅ ChatGPT (chat.openai.com)
- ✅ Claude.ai
- ✅ Poe.com
- ✅ Perplexity.ai
- ✅ Google Bard/Gemini
- ✅ HuggingChat
- ✅ Any text input on any website

## Technical Details

### Architecture
- **Manifest V3**: Modern Chrome extension format
- **Service Worker**: Background script for context menu
- **Content Script**: Text replacement in web pages
- **Enhancement Engine**: Core prompt optimization logic

### Files
```
prompt-enhancer-extension/
├── manifest.json          # Extension configuration
├── background.js          # Context menu & coordination
├── content.js            # Text selection & replacement
├── enhancer.js           # Core enhancement engine
├── popup.html            # Extension popup UI
├── popup.js              # Popup interactions
├── generate-icons.js     # Icon generation script
├── icons/                # Extension icons
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
└── README.md            # This file
```

### Permissions
- `contextMenus`: Right-click menu integration
- `activeTab`: Access to current tab content
- `scripting`: Text replacement capability
- `storage`: Enhancement statistics

## Keyboard Shortcuts ⌨️ **NEW in v1.1**

Super fast enhancement without clicking! Select text and use:

- **`Ctrl+Shift+E`** (`Cmd+Shift+E` on Mac): **Quick Enhance** - Repeats your last used mode
- **`Ctrl+Shift+Z`** (`Cmd+Shift+Z` on Mac): **Zero Shot Mode** - No questions allowed
- **`Ctrl+Shift+I`** (`Cmd+Shift+I` on Mac): **Interactive Mode** - Step-by-step
- **`Ctrl+Shift+C`** (`Cmd+Shift+C` on Mac): **Claude Optimize** - XML formatting

### Customize Shortcuts
1. Go to `chrome://extensions/shortcuts`
2. Find "Prompt Enhancer Pro"
3. Click pencil icon to change any shortcut
4. Set your preferred key combinations

**Pro Tip**: `Ctrl+Shift+E` learns your preference! It uses whichever mode you used last (via context menu or shortcut).

## Statistics

View enhancement statistics by clicking the extension icon:
- Total enhancements performed
- Available enhancement modes
- Usage instructions

## Troubleshooting

### Text Not Replacing
- Ensure text is selected before right-clicking
- Try selecting text in a different field (some sites block modification)
- Check if site uses shadow DOM (limited support)

### Context Menu Not Appearing
- Refresh the page
- Reload the extension from chrome://extensions/
- Check that extension is enabled

### Notification Not Showing
- Check browser notification permissions
- Some sites may block notifications

## Based On

This extension implements the systematic prompt engineering methodology from the Prompt Engineering Project, including:

- **Evaluation Rubrics**: 5-dimension scoring system
- **Anti-Pattern Detection**: Automatic issue identification
- **Platform Optimization**: Claude (XML), GPT-4 (JSON)
- **Mode Enforcement**: Zero Shot, Zero Shot Relaxed, Interactive
- **Structured Patterns**: Templates and proven structures

## Changelog

### v1.0.0 (2024-11-09)
- Initial release
- 9 enhancement modes
- Platform optimization (Claude, GPT-4)
- Anti-pattern fixing
- Evaluation & scoring
- Statistics tracking
- Visual notifications

## Future Enhancements

### v1.1 (Planned)
- [ ] Keyboard shortcuts
- [ ] Custom enhancement presets
- [ ] Enhancement history
- [ ] Export/import settings
- [ ] More platform optimizations (Gemini, Grok)

### v1.2 (Planned)
- [ ] Batch enhancement (multiple selections)
- [ ] Template library
- [ ] A/B comparison mode
- [ ] Integration with Claude Code

## Support

For issues or feature requests:
1. Check troubleshooting section
2. Review enhancement examples
3. Verify extension permissions
4. Test on different websites

## License

Based on Prompt Engineering Project guidelines.
For personal and commercial use.

---

**Made with systematic prompt engineering principles** ✨
