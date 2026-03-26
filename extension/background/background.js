// Knowledge Helper - Background Service Worker
// Handles context menu,// Handles context menu, message routing, and API proxy for content scripts

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
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === 'save-to-kb' || info.menuItemId === 'save-page-to-kb') {
    // Try to send message to content script
    try {
      await chrome.tabs.sendMessage(tab.id, {
        type: 'SHOW_SAVE_POPUP',
        data: {
          selection: info.selectionText || '',
          title: tab.title
        }
      });
    } catch (error) {
      // Content script not loaded - inject it
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ['content/content.js']
        });
        
        // Wait a bit then send message
        setTimeout(async () => {
          await chrome.tabs.sendMessage(tab.id, {
            type: 'SHOW_SAVE_POPUP',
            data: {
              selection: info.selectionText || '',
              title: tab.title
            }
          });
        }, 200);
      }
    }
  }
});

// Handle messages from popup and content scripts
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  // API request from popup
  if (msg.type === 'API_REQUEST') {
    handleApiRequest(msg.endpoint, msg.method, msg.data)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true; // Keep channel open for async response
  }
  
  // API request from content script (different type to distinguish)
  if (msg.type === 'CONTENT_API_REQUEST') {
    handleApiRequest(msg.endpoint, msg.method, msg.data)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
});

async function handleApiRequest(endpoint, method = 'GET', data = null) {
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json'
    }
  };

  if (data && method !== 'GET') {
    options.body = JSON.stringify(data);
  }

  const response = await fetch(`${SERVER_URL}${endpoint}`, options);
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  return response.json();
}
