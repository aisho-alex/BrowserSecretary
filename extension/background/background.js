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
      // Content script not loaded - inject it
      try {
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ['content/content.js']
        });
        
        setTimeout(async () => {
          try {
            await chrome.tabs.sendMessage(tab.id, {
              type: 'SHOW_SAVE_POPUP',
              data: {
                selection: info.selectionText || '',
                title: tab.title
              }
            });
          } catch (e) {
            console.error('Failed to send message:', e);
          }
        }, 200);
      } catch (e) {
        console.error('Failed to inject script:', e);
      }
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
