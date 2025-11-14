// Content script for Prompt Enhancer Pro
// Handles text selection and replacement in web pages

// Load the enhancer
const enhancer = new PromptEnhancer();

// Store the current selection range
let currentRange = null;
let currentSelection = null;

// Track selection to maintain range
document.addEventListener('mouseup', () => {
  const selection = window.getSelection();
  if (selection.toString().length > 0) {
    currentSelection = selection;
    currentRange = selection.getRangeAt(0);
  }
});

// Listen for enhancement requests from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'enhancePrompt') {
    enhanceAndReplace(request.text, request.mode);
  }
});

function enhanceAndReplace(text, mode) {
  if (!currentRange) {
    showNotification('Error: No text selection found', 'error');
    return;
  }

  try {
    // Enhance the prompt
    const enhancedText = enhancer.enhance(text, mode);
    
    // Get the mode name for notification
    const modeName = getModeDisplayName(mode);
    
    // Replace the selected text
    replaceSelectedText(enhancedText);
    
    // Show success notification
    showNotification(`✓ Prompt enhanced with ${modeName}`, 'success');
    
    // Clear selection
    window.getSelection().removeAllRanges();
    currentRange = null;
    
  } catch (error) {
    console.error('Enhancement error:', error);
    showNotification('Error: Failed to enhance prompt', 'error');
  }
}

function replaceSelectedText(newText) {
  // Delete the current selection
  currentRange.deleteContents();
  
  // Check if we're in a text input/textarea
  const activeElement = document.activeElement;
  const isEditable = activeElement.tagName === 'TEXTAREA' || 
                     activeElement.tagName === 'INPUT' ||
                     activeElement.isContentEditable;
  
  if (isEditable) {
    // For editable elements, use different approach
    if (activeElement.tagName === 'TEXTAREA' || activeElement.tagName === 'INPUT') {
      const start = activeElement.selectionStart;
      const end = activeElement.selectionEnd;
      const text = activeElement.value;
      
      activeElement.value = text.substring(0, start) + newText + text.substring(end);
      activeElement.selectionStart = activeElement.selectionEnd = start + newText.length;
      
      // Trigger input event for frameworks
      activeElement.dispatchEvent(new Event('input', { bubbles: true }));
    } else {
      // ContentEditable
      const textNode = document.createTextNode(newText);
      currentRange.insertNode(textNode);
      
      // Trigger input event
      activeElement.dispatchEvent(new Event('input', { bubbles: true }));
    }
  } else {
    // For non-editable content, insert text node
    const textNode = document.createTextNode(newText);
    currentRange.insertNode(textNode);
  }
}

function getModeDisplayName(mode) {
  const names = {
    'zero_shot': 'Zero Shot Mode',
    'zero_shot_relaxed': 'Zero Shot Relaxed',
    'interactive': 'Interactive Mode',
    'claude_optimize': 'Claude Optimization',
    'gpt4_optimize': 'GPT-4 Optimization',
    'fix_antipatterns': 'Anti-Pattern Fixes',
    'add_structure': 'Structure Enhancement',
    'evaluate_score': 'Evaluation & Scoring'
  };
  return names[mode] || mode;
}

function showNotification(message, type = 'info') {
  // Create notification element
  const notification = document.createElement('div');
  notification.className = `prompt-enhancer-notification ${type}`;
  notification.textContent = message;
  
  // Style the notification
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 12px 20px;
    background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
    color: white;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    z-index: 999999;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 14px;
    font-weight: 500;
    animation: slideIn 0.3s ease-out;
  `;
  
  // Add animation
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from {
        transform: translateX(400px);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
    @keyframes slideOut {
      from {
        transform: translateX(0);
        opacity: 1;
      }
      to {
        transform: translateX(400px);
        opacity: 0;
      }
    }
  `;
  
  if (!document.querySelector('#prompt-enhancer-styles')) {
    style.id = 'prompt-enhancer-styles';
    document.head.appendChild(style);
  }
  
  // Add to page
  document.body.appendChild(notification);
  
  // Auto-remove after 3 seconds
  setTimeout(() => {
    notification.style.animation = 'slideOut 0.3s ease-in';
    setTimeout(() => {
      notification.remove();
    }, 300);
  }, 3000);
}

// Initialize
console.log('Prompt Enhancer Pro: Content script loaded');
