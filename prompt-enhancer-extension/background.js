// Background service worker for Prompt Enhancer Pro

// Enhancement modes based on project guidelines
const ENHANCEMENT_MODES = {
  ZERO_SHOT: 'zero_shot',
  ZERO_SHOT_RELAXED: 'zero_shot_relaxed',
  INTERACTIVE: 'interactive',
  CLAUDE_OPTIMIZE: 'claude_optimize',
  GPT4_OPTIMIZE: 'gpt4_optimize',
  FIX_ANTIPATTERNS: 'fix_antipatterns',
  ADD_STRUCTURE: 'add_structure',
  PLATFORM_CONVERT: 'platform_convert',
  EVALUATE_SCORE: 'evaluate_score'
};

// Create context menu on installation
chrome.runtime.onInstalled.addListener(() => {
  // Remove all existing menus first to prevent duplicate ID errors
  chrome.contextMenus.removeAll(() => {
    createContextMenus();
  });
});

// Also recreate menus on startup (service worker wake)
chrome.runtime.onStartup.addListener(() => {
  chrome.contextMenus.removeAll(() => {
    createContextMenus();
  });
});

function createContextMenus() {
  // Parent menu
  chrome.contextMenus.create({
    id: 'promptEnhance',
    title: 'Prompt Enhance',
    contexts: ['selection']
  });

  // Mode Enhancement submenu
  chrome.contextMenus.create({
    id: 'modeEnhance',
    parentId: 'promptEnhance',
    title: 'Enforce Mode',
    contexts: ['selection']
  });

  chrome.contextMenus.create({
    id: ENHANCEMENT_MODES.ZERO_SHOT,
    parentId: 'modeEnhance',
    title: '🎯 Zero Shot (No Questions)',
    contexts: ['selection']
  });

  chrome.contextMenus.create({
    id: ENHANCEMENT_MODES.ZERO_SHOT_RELAXED,
    parentId: 'modeEnhance',
    title: '🎯 Zero Shot Relaxed (1 Question OK)',
    contexts: ['selection']
  });

  chrome.contextMenus.create({
    id: ENHANCEMENT_MODES.INTERACTIVE,
    parentId: 'modeEnhance',
    title: '💬 Interactive (Step-by-Step)',
    contexts: ['selection']
  });

  // Platform Optimization submenu
  chrome.contextMenus.create({
    id: 'platformOptimize',
    parentId: 'promptEnhance',
    title: 'Optimize for Platform',
    contexts: ['selection']
  });

  chrome.contextMenus.create({
    id: ENHANCEMENT_MODES.CLAUDE_OPTIMIZE,
    parentId: 'platformOptimize',
    title: '🤖 Optimize for Claude',
    contexts: ['selection']
  });

  chrome.contextMenus.create({
    id: ENHANCEMENT_MODES.GPT4_OPTIMIZE,
    parentId: 'platformOptimize',
    title: '🧠 Optimize for GPT-4',
    contexts: ['selection']
  });

  // Quick Fixes
  chrome.contextMenus.create({
    id: 'quickFixes',
    parentId: 'promptEnhance',
    title: 'Quick Fixes',
    contexts: ['selection']
  });

  chrome.contextMenus.create({
    id: ENHANCEMENT_MODES.FIX_ANTIPATTERNS,
    parentId: 'quickFixes',
    title: '🔧 Fix Anti-Patterns',
    contexts: ['selection']
  });

  chrome.contextMenus.create({
    id: ENHANCEMENT_MODES.ADD_STRUCTURE,
    parentId: 'quickFixes',
    title: '📋 Add Structure & Format',
    contexts: ['selection']
  });

  // Advanced
  chrome.contextMenus.create({
    id: ENHANCEMENT_MODES.EVALUATE_SCORE,
    parentId: 'promptEnhance',
    title: '📊 Evaluate & Score',
    contexts: ['selection']
  });
}

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'promptEnhance') return;
  if (info.menuItemId === 'modeEnhance') return;
  if (info.menuItemId === 'platformOptimize') return;
  if (info.menuItemId === 'quickFixes') return;

  const selectedText = info.selectionText;
  const mode = info.menuItemId;

  // Store last used mode for keyboard shortcuts
  chrome.storage.local.set({ lastUsedMode: mode });

  // Enhance the text
  enhanceText(tab.id, selectedText, mode);
});

// Handle keyboard shortcuts
chrome.commands.onCommand.addListener((command) => {
  // Get the active tab
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (!tabs[0]) return;

    const tab = tabs[0];

    // Execute script to get selected text
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => window.getSelection().toString()
    }).then((results) => {
      const selectedText = results[0]?.result;

      if (!selectedText || selectedText.trim() === '') {
        // Show notification if no text is selected
        chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: (message) => {
            const notification = document.createElement('div');
            notification.textContent = message;
            notification.style.cssText = 'position:fixed;top:20px;right:20px;background:#ef4444;color:white;padding:16px 24px;border-radius:8px;z-index:999999;font-family:system-ui;box-shadow:0 4px 12px rgba(0,0,0,0.2);';
            document.body.appendChild(notification);
            setTimeout(() => notification.remove(), 3000);
          },
          args: ['⚠️ Please select some text first']
        });
        return;
      }

      // Determine which mode to use
      let mode;

      switch (command) {
        case 'enhance-zero-shot':
          mode = ENHANCEMENT_MODES.ZERO_SHOT;
          break;
        case 'enhance-interactive':
          mode = ENHANCEMENT_MODES.INTERACTIVE;
          break;
        case 'enhance-claude':
          mode = ENHANCEMENT_MODES.CLAUDE_OPTIMIZE;
          break;
        case 'enhance-last-used':
          // Get last used mode from storage
          chrome.storage.local.get(['lastUsedMode'], (result) => {
            const lastMode = result.lastUsedMode || ENHANCEMENT_MODES.FIX_ANTIPATTERNS;
            enhanceText(tab.id, selectedText, lastMode);
          });
          return; // Early return to avoid calling enhanceText below
        default:
          return;
      }

      // Store last used mode
      chrome.storage.local.set({ lastUsedMode: mode });

      // Enhance the text
      enhanceText(tab.id, selectedText, mode);
    }).catch(err => {
      console.error('Failed to get selected text:', err);
    });
  });
});

// Helper function to enhance text
function enhanceText(tabId, text, mode) {
  // Increment statistics
  chrome.storage.local.get(['enhancementCount'], (result) => {
    const count = (result.enhancementCount || 0) + 1;
    chrome.storage.local.set({ enhancementCount: count });
  });

  // Send message to content script to enhance and replace text
  chrome.tabs.sendMessage(tabId, {
    action: 'enhancePrompt',
    text: text,
    mode: mode
  }, (response) => {
    // Handle case where content script isn't loaded
    if (chrome.runtime.lastError) {
      console.log('Content script not ready:', chrome.runtime.lastError.message);
      // Try to inject content scripts manually
      chrome.scripting.executeScript({
        target: { tabId: tabId },
        files: ['enhancer.js', 'content.js']
      }).then(() => {
        // Retry sending message after injection
        chrome.tabs.sendMessage(tabId, {
          action: 'enhancePrompt',
          text: text,
          mode: mode
        });
      }).catch(err => {
        console.error('Failed to inject content script:', err);
      });
    }
  });
}
