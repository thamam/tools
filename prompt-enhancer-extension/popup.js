// Popup script for Prompt Enhancer Pro

// Load and display statistics
document.addEventListener('DOMContentLoaded', () => {
  loadStats();
  
  // Reset button
  document.getElementById('resetStats').addEventListener('click', resetStats);
});

function loadStats() {
  chrome.storage.local.get(['enhancementCount'], (result) => {
    const count = result.enhancementCount || 0;
    document.getElementById('enhancementsCount').textContent = count;
  });
}

function resetStats() {
  if (confirm('Reset enhancement statistics?')) {
    chrome.storage.local.set({ enhancementCount: 0 }, () => {
      document.getElementById('enhancementsCount').textContent = '0';
      
      // Show confirmation
      const button = document.getElementById('resetStats');
      const originalText = button.textContent;
      button.textContent = '✓ Reset Complete';
      button.style.background = 'rgba(16, 185, 129, 0.3)';
      
      setTimeout(() => {
        button.textContent = originalText;
        button.style.background = '';
      }, 2000);
    });
  }
}
