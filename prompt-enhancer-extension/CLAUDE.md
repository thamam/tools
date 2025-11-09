# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Chrome Extension (Manifest V3) that enhances prompts using systematic prompt engineering principles. It provides context menu integration to transform selected text with various enhancement modes including interaction enforcement, platform optimization, anti-pattern fixing, and quality evaluation.

## Architecture

### Core Components

**PromptEnhancer** (`enhancer.js`): Central enhancement engine with 10 methods
- Mode enforcement: `enforceZeroShot()`, `enforceZeroShotRelaxed()`, `enforceInteractive()`
- Platform optimization: `optimizeForClaude()`, `optimizeForGPT4()`
- Quality improvements: `fixAntiPatterns()`, `addStructure()`
- Analysis: `analyzePrompt()`, `evaluatePrompt()`
- Entry point: `enhance(mode, prompt)` - Routes to appropriate enhancement method

**Message Flow**:
1. User right-clicks selected text → `background.js` creates context menu
2. Menu selection triggers → `background.js` sends message to content script
3. `content.js` receives message → calls `enhancer.enhance(mode, selectedText)`
4. Enhanced text → `content.js` replaces selection in DOM
5. Visual notification → confirms enhancement

**DOM Replacement Strategy** (`content.js`):
- Maintains `currentSelection` and `currentRange` on mouseup
- `replaceSelectedText()` handles multiple element types:
  - Textareas/inputs: Direct value replacement
  - ContentEditable: Range-based text node manipulation
  - Fallback: Clipboard-based replacement

### Enhancement Modes (9 total)

Defined in `ENHANCEMENT_MODES` constant (background.js:3-13):
- `ZERO_SHOT`: No questions allowed, immediate execution
- `ZERO_SHOT_RELAXED`: One clarification question permitted
- `INTERACTIVE`: Step-by-step with mandatory checkpoints
- `CLAUDE_OPTIMIZE`: XML-structured format for Claude
- `GPT4_OPTIMIZE`: JSON-structured format for GPT-4
- `FIX_ANTIPATTERNS`: Detects and fixes vague verbs, missing output formats, success criteria
- `ADD_STRUCTURE`: Adds comprehensive prompt structure
- `PLATFORM_CONVERT`: Platform-specific formatting (future use)
- `EVALUATE_SCORE`: 4-dimension quality scoring (Clarity, Specificity, Completeness, Efficiency)

## Development Commands

### Icon Generation (Required for installation)
```bash
node generate-icons.js
```
Generates 16x16, 48x48, and 128x128 PNG icons in `icons/` directory. Must run before loading extension.

### Load Extension for Development
1. Generate icons (if not done): `node generate-icons.js`
2. Navigate to `chrome://extensions/`
3. Enable "Developer mode" (top-right toggle)
4. Click "Load unpacked"
5. Select this directory

### Testing Changes
After modifying code:
1. Go to `chrome://extensions/`
2. Click reload icon on "Prompt Enhancer Pro"
3. Refresh any open tabs where you want to test
4. Select text and test via right-click menu

### Package for Distribution
```bash
zip -r prompt-enhancer-pro.zip . -x "*.git*" -x "node_modules/*" -x "generate-icons.js"
```

## Code Patterns

### Adding New Enhancement Mode

1. **Add mode constant** to `ENHANCEMENT_MODES` (background.js:3-13)
2. **Create enhancement method** in `PromptEnhancer` class (enhancer.js)
3. **Add case** to `enhance()` switch statement (enhancer.js:350-371)
4. **Add context menu item** in background.js chrome.runtime.onInstalled listener
5. **Update mode display name** in content.js `getModeDisplayName()` if needed

### Content Script Communication
Messages from background.js follow this schema:
```javascript
{
  action: "enhance",
  mode: ENHANCEMENT_MODES.*,
  text: selectedText
}
```

### DOM Manipulation Safety
Always check element type before replacement:
- Use `element.value` for input/textarea
- Use `document.execCommand()` or Range API for contentEditable
- Fallback to clipboard operations for unknown types

## File Structure

```
prompt-enhancer-extension/
├── manifest.json          # Extension manifest (V3)
├── background.js          # Service worker: context menu coordination
├── content.js            # Content script: text selection & DOM replacement
├── enhancer.js           # PromptEnhancer class: core enhancement logic
├── popup.html            # Extension popup UI
├── popup.js              # Popup statistics & interactions
├── generate-icons.js     # Icon generation utility (Node.js)
├── icons/                # Generated extension icons
└── README.md            # User documentation
```

## Manifest V3 Considerations

- Background script runs as **service worker** (not persistent)
- Content scripts injected via `content_scripts` in manifest
- No inline JavaScript in HTML files
- Uses `chrome.scripting` for dynamic content injection
- All frames supported (`all_frames: true`)

## Browser Compatibility

- Works on all URLs (`<all_urls>` permission)
- Tested platforms: ChatGPT, Claude.ai, Poe, Perplexity, Bard/Gemini, HuggingChat
- Supports: textareas, inputs, contentEditable, CodeMirror, Monaco editors

## Common Issues

**Text not replacing**: Some sites use shadow DOM or block modifications. The extension attempts multiple replacement strategies but may fail on heavily restricted sites.

**Context menu not appearing**: Extension must be reloaded after code changes. Content scripts only inject on page load.

**Notification positioning**: Uses fixed positioning (top-right). Some sites with z-index conflicts may hide notifications.
