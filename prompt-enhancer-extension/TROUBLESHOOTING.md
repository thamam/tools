# Troubleshooting Guide

## Common Issues and Solutions

### Extension Not Loading

#### Symptom
Extension doesn't appear in `chrome://extensions/` or shows errors

#### Solutions

**1. Check Required Files**
```bash
cd ~/Applications/prompt-enhancer-extension
ls -la manifest.json background.js content.js enhancer.js popup.html icons/
```
All files should exist. If icons are missing:
```bash
node generate-icons.js
```

**2. Verify Manifest**
```bash
cat manifest.json | python3 -m json.tool
```
Should output valid JSON without errors.

**3. Check JavaScript Syntax**
```bash
node -c background.js && node -c content.js && node -c enhancer.js
```
Should complete without errors.

**4. Developer Mode Must Be Enabled**
1. Go to `chrome://extensions/`
2. Toggle "Developer mode" ON (top-right)
3. Click "Load unpacked"
4. Select the `prompt-enhancer-extension` directory

---

### "Duplicate ID" Errors in Console

#### Symptom
Extension loads but shows errors like:
```
Error: Cannot create item with duplicate id promptEnhance
```

#### Solution
This was fixed in the latest version. Update your `background.js`:

**What Changed**: Added `chrome.contextMenus.removeAll()` before creating menus to prevent duplicates when extension reloads.

**To Update**:
1. Copy the latest `background.js` from the repository
2. Or pull latest changes: `git pull origin main`
3. Reload extension in `chrome://extensions/`

---

### Context Menu Not Appearing

#### Symptom
Right-click on selected text, no "Prompt Enhance" menu

#### Solutions

**1. Refresh the Page**
Content scripts only inject on page load. After loading/reloading extension:
- Refresh any open tabs (`Ctrl+R` or `Cmd+R`)

**2. Check Selection**
- Ensure text is actually selected (highlighted)
- Menu only appears with `contexts: ['selection']`

**3. Check Extension Errors**
1. Go to `chrome://extensions/`
2. Click "Errors" button on the extension
3. Look for console errors
4. Common error: "Cannot create item with duplicate id" → See above

**4. Verify Extension is Enabled**
- In `chrome://extensions/`, ensure toggle is ON

**5. Reload Extension**
1. Go to `chrome://extensions/`
2. Click reload icon (circular arrow) on the extension
3. Refresh your webpage
4. Try right-clicking selected text again

---

### Text Not Replacing

#### Symptom
Menu appears, click enhancement, but text doesn't change

#### Solutions

**1. Check Console**
- Right-click page → Inspect → Console tab
- Look for errors related to the extension

**2. Site May Block Modifications**
Some sites (especially `chrome://` pages) block content script modifications:
- ❌ Won't work: `chrome://extensions/`, `chrome://settings/`
- ✅ Should work: ChatGPT, Claude.ai, Google Docs, most websites

**3. Content Script Not Loaded**
The latest version auto-injects scripts if missing. If using older version:
1. Refresh the page
2. Try selection again

**4. Check for JavaScript Errors**
Open DevTools Console (F12), look for:
```
enhancer is not defined
PromptEnhancer is not defined
```
This means content scripts didn't load. Solution:
- Reload extension in `chrome://extensions/`
- Refresh webpage
- Try again

---

### Service Worker Errors

#### Symptom
Extension works initially but stops after a while

#### Explanation
Manifest V3 service workers are non-persistent and may deactivate. The extension now handles this automatically.

#### Solutions

**1. Check Service Worker Status**
1. Go to `chrome://extensions/`
2. Find "Prompt Enhancer Pro"
3. Click "Service Worker" link
4. See if it shows "inactive"

**2. Wake Service Worker**
- Right-click any selected text
- This will wake the service worker

**3. Use Latest Version**
The updated `background.js` now includes:
- `chrome.runtime.onStartup` listener
- Auto-recreation of context menus on wake

---

### Icons Missing or Broken

#### Symptom
Extension shows broken image icon

#### Solution

**Generate Icons**:
```bash
cd ~/Applications/prompt-enhancer-extension
node generate-icons.js
```

This creates:
- `icons/icon16.png`
- `icons/icon48.png`
- `icons/icon128.png`

**Verify Icons Exist**:
```bash
ls -la icons/*.png
```

**Reload Extension**:
1. `chrome://extensions/`
2. Click reload icon
3. Icons should appear

---

### "Cannot access chrome:// URLs" Error

#### Symptom
Error when trying to use extension on Chrome system pages

#### Explanation
This is a Chrome security restriction. Extensions cannot run on:
- `chrome://extensions/`
- `chrome://settings/`
- `chrome://flags/`
- Chrome Web Store pages

#### Solution
Use the extension on regular websites:
- ✅ ChatGPT.com
- ✅ Claude.ai
- ✅ Google Docs
- ✅ Any normal webpage

---

### Notification Not Showing

#### Symptom
Enhancement works but no success notification appears

#### Causes
1. Site CSS conflicts
2. Z-index issues
3. Browser notification permissions

#### Solution
Check `content.js` notification styling. Default position: top-right with z-index 999999.

If notifications are blocked:
1. Click site permissions (lock icon in address bar)
2. Allow notifications for the site

---

### Extension Slowing Down Page

#### Symptom
Web pages load slowly after installing extension

#### Explanation
Extension injects content scripts on all pages (`<all_urls>`)

#### Solutions

**1. Optimize Injection**
Edit `manifest.json` to only inject on specific sites:
```json
"content_scripts": [{
  "matches": [
    "https://chat.openai.com/*",
    "https://claude.ai/*"
  ],
  "js": ["enhancer.js", "content.js"]
}]
```

**2. Lazy Loading**
Content scripts only run when needed (context menu click)

---

### Chrome Extension Best Practices

#### Reload Extension After Every Code Change
1. Edit code
2. Go to `chrome://extensions/`
3. Click reload button
4. Refresh any open tabs
5. Test changes

#### Clear Console Errors
- Inspect → Console → Clear
- Helps identify new vs old errors

#### Test in Incognito Mode
- Rules out conflicts with other extensions
- Right-click extension → "Allow in incognito"

#### Check Extension Logs
1. `chrome://extensions/`
2. Click "Service Worker" (for background.js)
3. Click "Inspect views" (for content scripts)

---

## Debugging Checklist

When extension isn't working:

- [ ] Developer mode enabled in `chrome://extensions/`
- [ ] Extension appears in extensions list
- [ ] Extension toggle is ON (blue)
- [ ] No red error messages in extension card
- [ ] Icons display correctly (not broken images)
- [ ] Page has been refreshed after loading extension
- [ ] Text is actually selected before right-clicking
- [ ] Not trying to use on `chrome://` pages
- [ ] Service worker is active (check "Service Worker" link)
- [ ] Console shows no JavaScript errors (F12 → Console)
- [ ] `manifest.json` is valid JSON
- [ ] All required files exist (manifest.json, background.js, content.js, enhancer.js, popup.html)
- [ ] Icons exist in `icons/` directory

---

## Getting More Help

### 1. Check Extension Console
```
chrome://extensions/ → Prompt Enhancer Pro → Errors button
```

### 2. Check Page Console
```
Right-click page → Inspect → Console tab
```

### 3. Check Service Worker Console
```
chrome://extensions/ → Service Worker link → Opens DevTools
```

### 4. Enable Verbose Logging
Add to `background.js`:
```javascript
console.log('Extension loaded');
console.log('Context menus created');
```

Add to `content.js`:
```javascript
console.log('Content script loaded');
console.log('Message received:', message);
```

---

## Fixed Issues (Latest Version)

### ✅ Duplicate Context Menu IDs
**Fixed**: Added `chrome.contextMenus.removeAll()` before creation

### ✅ Content Scripts Not Loading
**Fixed**: Auto-injection fallback in `background.js`

### ✅ Service Worker Not Waking
**Fixed**: Added `chrome.runtime.onStartup` listener

---

## Still Having Issues?

1. **Try a Clean Install**:
   ```bash
   # Remove extension from chrome://extensions/
   # Delete and re-clone repository
   git clone <repo-url>
   cd prompt-enhancer-extension
   node generate-icons.js
   # Load unpacked in Chrome
   ```

2. **Test on Minimal Page**:
   - Create simple HTML file
   - Add textarea
   - Try enhancement there
   - Rules out site-specific issues

3. **Check Chrome Version**:
   - Extension requires Chrome 88+ (Manifest V3)
   - Check: `chrome://version/`

---

**Last Updated**: 2025-11-09
**Version**: 1.0.1 (with fixes)
