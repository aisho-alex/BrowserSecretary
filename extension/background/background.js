// Knowledge Helper - Background Service Worker
// Handles context menu, message routing, and API proxy for content scripts

const SERVER_URL = 'http://127.0.0.1:8000';

// Create context menu on install
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'save-to-kb',
    title: '📚 Save to Knowledge Base',
    contexts: ['selection']
  });

  chrome.contextMenus.create({
    id: 'save-page-to-kb',
    title: '📚 Save Page to Knowledge Base',
    contexts: ['page']
  });

  // Q&A context menu
  chrome.contextMenus.create({
    id: 'qa-selection',
    title: '❓ Ask about selection',
    contexts: ['selection']
  });

  chrome.contextMenus.create({
    id: 'qa-page',
    title: '🤖 Q&A Assistant',
    contexts: ['page']
  });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === 'save-to-kb' || info.menuItemId === 'save-page-to-kb') {
    try {
      await chrome.tabs.sendMessage(tab.id, {
        type: 'SHOW_SAVE_POPUP',
        data: {
          selection: info.selectionText || '',
          title: tab.title
        }
      });
    } catch (error) {
      // Content script not loaded - inject it first
      try {
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ['content/content.js', 'content/qa-content.js']
        });
        // Wait a bit for scripts to load
        await new Promise(resolve => setTimeout(resolve, 100));
        await chrome.tabs.sendMessage(tab.id, {
          type: 'SHOW_SAVE_POPUP',
          data: {
            selection: info.selectionText || '',
            title: tab.title
          }
        });
      } catch (injectError) {
        console.error('Failed to inject and send message:', injectError);
      }
    }
  }

  // Q&A menu items
  if (info.menuItemId === 'qa-selection') {
    try {
      const response = await chrome.tabs.sendMessage(tab.id, {
        type: 'ASK_ABOUT_SELECTION',
        data: {
          selection: info.selectionText || ''
        }
      });
      // Don't wait for response, just send
    } catch (error) {
      // Content script not loaded - inject it first
      try {
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ['content/content.js', 'content/qa-content.js']
        });
        await new Promise(resolve => setTimeout(resolve, 100));
        await chrome.tabs.sendMessage(tab.id, {
          type: 'ASK_ABOUT_SELECTION',
          data: {
            selection: info.selectionText || ''
          }
        });
      } catch (injectError) {
        console.error('Failed to inject and send Q&A message:', injectError);
      }
    }
  }

  if (info.menuItemId === 'qa-page') {
    try {
      await chrome.tabs.sendMessage(tab.id, {
        type: 'OPEN_QA_PANEL'
      });
    } catch (error) {
      // Content script not loaded - inject it first
      try {
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ['content/content.js', 'content/qa-content.js']
        });
        await new Promise(resolve => setTimeout(resolve, 100));
        await chrome.tabs.sendMessage(tab.id, {
          type: 'OPEN_QA_PANEL'
        });
      } catch (injectError) {
        console.error('Failed to inject and open Q&A panel:', injectError);
      }
    }
  }
});

// Handle keyboard commands
chrome.commands.onCommand.addListener(async (command, tab) => {
  if (command === 'toggle-qa-panel') {
    try {
      await chrome.tabs.sendMessage(tab.id, {
        type: 'OPEN_QA_PANEL'
      });
    } catch (error) {
      console.error('Failed to toggle Q&A panel:', error);
    }
  }
});

// Handle messages from popup and content scripts
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'API_REQUEST' || msg.type === 'CONTENT_API_REQUEST') {
    handleApiRequest(msg.endpoint, msg.method, msg.data)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
  
  // Handle page content requests
  if (msg.type === 'GET_PAGE_CONTENT') {
    chrome.tabs.sendMessage(sender.tab.id, { type: 'PAGE_CONTENT_REQUESTED' }, (response) => {
      if (chrome.runtime.lastError) {
        sendResponse({ success: false, error: chrome.runtime.lastError.message });
      } else {
        sendResponse({ success: true, data: response });
      }
    });
    return true;
  }
  
  return false;
});

async function handleApiRequest(endpoint, method = 'GET', data = null) {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' }
  };

  if (data && method !== 'GET') {
    options.body = JSON.stringify(data);
  }

  const response = await fetch(`${SERVER_URL}${endpoint}`, options);

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorText}`);
  }

  return response.json();
}
