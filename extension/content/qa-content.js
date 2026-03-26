// Knowledge Helper - Q&A Content Script
// Handles in-page Q&A panel and smart content extraction

class KnowledgeHelperQA {
  constructor() {
    this.sidePanel = null;
    this.quickPopup = null;
    this.selectedText = '';
    this.pageContent = '';
    this.chatHistory = [];
    this.projects = [];
    this.init();
  }

  init() {
    // Listen for messages from background
    chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
      if (msg.type === 'OPEN_QA_PANEL') {
        this.toggleSidePanel();
        sendResponse({ success: true });
      } else if (msg.type === 'ASK_ABOUT_SELECTION') {
        this.showQuickPopup(msg.data.selection);
        sendResponse({ success: true });
      } else if (msg.type === 'PAGE_CONTENT_REQUESTED') {
        this.extractPageContent();
        sendResponse({ content: this.pageContent, url: window.location.href, title: document.title });
      }
      return true;
    });

    // Track text selection
    document.addEventListener('mouseup', () => {
      const selection = window.getSelection().toString().trim();
      this.selectedText = selection;
    });

    // Keyboard shortcut: Ctrl+Shift+K to toggle Q&A panel
    document.addEventListener('keydown', (e) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'K') {
        e.preventDefault();
        this.toggleSidePanel();
      }
    });
  }

  // =========================================================================
  // Smart Content Extraction
  // =========================================================================

  extractPageContent() {
    // Remove script, style, nav, header, footer, ads
    const clone = document.cloneNode(true);
    const selectorsToRemove = [
      'script', 'style', 'nav', 'header', 'footer',
      '[class*="ad"]', '[id*="ad"]', '.advertisement', '.sidebar',
      '.menu', '.navigation', '.cookie-banner', '[class*="social"]'
    ];

    selectorsToRemove.forEach(selector => {
      clone.querySelectorAll(selector).forEach(el => el.remove());
    });

    // Get main content area if exists
    const mainElement = clone.querySelector('main') || 
                        clone.querySelector('article') || 
                        clone.querySelector('[role="main"]') ||
                        clone.querySelector('.content') ||
                        clone.querySelector('#content');

    this.pageContent = mainElement 
      ? mainElement.textContent.trim()
      : clone.body.textContent.trim();

    // Clean up whitespace
    this.pageContent = this.pageContent.replace(/\s+/g, ' ').slice(0, 10000);
    
    return this.pageContent;
  }

  // =========================================================================
  // Side Panel (Chat Interface)
  // =========================================================================

  toggleSidePanel() {
    if (this.sidePanel) {
      this.sidePanel.remove();
      this.sidePanel = null;
      return;
    }

    this.sidePanel = document.createElement('div');
    this.sidePanel.className = 'kh-qa-side-panel';
    this.sidePanel.innerHTML = `
      <div class="kh-qa-panel-header">
        <h3>🤖 Q&A Assistant</h3>
        <div class="kh-qa-header-actions">
          <button class="kh-qa-minimize" title="Minimize">−</button>
          <button class="kh-qa-close" title="Close">×</button>
        </div>
      </div>
      <div class="kh-qa-chat-container">
        <div class="kh-qa-chat-messages" id="kh-qa-messages">
          <div class="kh-qa-welcome-message">
            <p>👋 Привет! Я помогу вам разобраться в содержании этой страницы.</p>
            <p class="kh-qa-page-info">
              <strong>Страница:</strong> ${document.title}<br>
              <strong>URL:</strong> ${window.location.href.slice(0, 50)}...
            </p>
          </div>
        </div>
        <div class="kh-qa-input-container">
          <textarea 
            id="kh-qa-question" 
            placeholder="Задайте вопрос по содержанию страницы..." 
            rows="3"
          ></textarea>
          <div class="kh-qa-input-actions">
            <button class="kh-qa-btn kh-qa-btn-secondary" id="kh-qa-clear">Очистить</button>
            <button class="kh-qa-btn kh-qa-btn-primary" id="kh-qa-ask">
              <span>Задать вопрос</span>
              <span class="kh-qa-loading" style="display:none">⏳</span>
            </button>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(this.sidePanel);
    this.setupSidePanelHandlers();
    
    // Load projects for save functionality
    this.loadProjects();
  }

  setupSidePanelHandlers() {
    const panel = this.sidePanel;

    // Close button
    panel.querySelector('.kh-qa-close').addEventListener('click', () => {
      this.toggleSidePanel();
    });

    // Minimize button
    panel.querySelector('.kh-qa-minimize').addEventListener('click', () => {
      panel.classList.toggle('kh-qa-minimized');
    });

    // Ask button
    panel.querySelector('#kh-qa-ask').addEventListener('click', () => this.askQuestion());

    // Clear button
    panel.querySelector('#kh-qa-clear').addEventListener('click', () => {
      this.chatHistory = [];
      const messagesContainer = panel.querySelector('#kh-qa-messages');
      messagesContainer.innerHTML = `
        <div class="kh-qa-welcome-message">
          <p>👋 Привет! Я помогу вам разобраться в содержании этой страницы.</p>
        </div>
      `;
    });

    // Enter to send (Shift+Enter for new line)
    panel.querySelector('#kh-qa-question').addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.askQuestion();
      }
    });
  }

  async loadProjects() {
    try {
      const projects = await this.apiRequest('/api/projects/');
      this.projects = projects;
    } catch (error) {
      console.error('[Knowledge Helper Q&A] Failed to load projects:', error);
    }
  }

  async askQuestion() {
    const panel = this.sidePanel;
    const questionInput = panel.querySelector('#kh-qa-question');
    const question = questionInput.value.trim();
    const askBtn = panel.querySelector('#kh-qa-ask');
    const loadingIndicator = askBtn.querySelector('.kh-qa-loading');

    if (!question) return;

    // Add user message to chat
    this.addChatMessage('user', question);
    questionInput.value = '';

    // Show loading
    askBtn.disabled = true;
    loadingIndicator.style.display = 'inline';

    try {
      // Extract page content for context
      const pageContent = this.extractPageContent();

      // Send to Q&A API
      const response = await this.apiRequest('/api/qa/', 'POST', {
        question: question,
        context: pageContent,
        url: window.location.href,
        page_title: document.title
      });

      // Add assistant response
      this.addChatMessage('assistant', response.answer, response.sources);

    } catch (error) {
      this.addChatMessage('error', `Ошибка: ${error.message}`);
    } finally {
      askBtn.disabled = false;
      loadingIndicator.style.display = 'none';
    }
  }

  addChatMessage(role, content, sources = null) {
    const messagesContainer = this.sidePanel.querySelector('#kh-qa-messages');
    const messageEl = document.createElement('div');
    messageEl.className = `kh-qa-message kh-qa-message-${role}`;

    let sourcesHtml = '';
    if (sources && sources.length > 0) {
      sourcesHtml = `
        <div class="kh-qa-sources">
          <strong>Источники:</strong>
          <ul>
            ${sources.map(s => `
              <li>
                <a href="#" data-source-id="${s.id}">${this.escapeHtml(s.title)}</a>
                ${s.tags && s.tags.length ? `<span class="kh-qa-tags">${s.tags.map(t => `#${t}`).join(' ')}</span>` : ''}
              </li>
            `).join('')}
          </ul>
        </div>
      `;
    }

    // Save button for assistant messages
    let saveButtonHtml = '';
    if (role === 'assistant') {
      saveButtonHtml = `
        <div class="kh-qa-message-actions">
          <button class="kh-qa-save-btn" title="Сохранить в базу знаний">
            💾 Сохранить
          </button>
        </div>
      `;
    }

    messageEl.innerHTML = `
      <div class="kh-qa-message-content">
        ${this.escapeHtml(content)}
      </div>
      ${sourcesHtml}
      ${saveButtonHtml}
    `;

    messagesContainer.appendChild(messageEl);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Setup save button handler
    if (role === 'assistant') {
      messageEl.querySelector('.kh-qa-save-btn').addEventListener('click', () => {
        this.saveToKnowledgeBase(content, sources);
      });
    }

    // Store in history
    this.chatHistory.push({ role, content, sources, timestamp: new Date().toISOString() });
  }

  async saveToKnowledgeBase(content, sources) {
    if (this.projects.length === 0) {
      await this.loadProjects();
    }

    // Create save popup
    const popup = document.createElement('div');
    popup.className = 'kh-qa-save-popup';
    popup.innerHTML = `
      <div class="kh-qa-save-popup-content">
        <div class="kh-qa-save-popup-header">
          <h4>💾 Сохранить в базу знаний</h4>
          <div class="kh-qa-popup-controls">
            <button class="kh-qa-popup-minimize" title="Свернуть">−</button>
            <button class="kh-qa-popup-close" title="Закрыть">×</button>
          </div>
        </div>
        <div class="kh-form-group">
          <label>Проект</label>
          <select id="kh-qa-save-project">
            ${this.projects.length 
              ? this.projects.map(p => `<option value="${p.id}">${this.escapeHtml(p.name)}</option>`).join('')
              : '<option value="">Нет проектов</option>'
            }
          </select>
        </div>
        <div class="kh-form-group">
          <label>Заголовок</label>
          <input type="text" id="kh-qa-save-title" placeholder="Введите заголовок..." 
                 value="Q&A: ${document.title.slice(0, 30)}...">
        </div>
        <div class="kh-form-group">
          <label>Содержание</label>
          <textarea id="kh-qa-save-content" rows="5">${this.escapeHtml(content)}</textarea>
        </div>
        <div class="kh-form-group">
          <label>Теги</label>
          <input type="text" id="kh-qa-save-tags" placeholder="qa, вопрос, ответ">
        </div>
        <div class="kh-qa-save-actions">
          <button class="kh-qa-btn kh-qa-btn-secondary" id="kh-qa-save-cancel">Отмена</button>
          <button class="kh-qa-btn kh-qa-btn-primary" id="kh-qa-save-confirm">Сохранить</button>
        </div>
      </div>
    `;

    document.body.appendChild(popup);
    this.makeDraggable(popup);
    this.centerPopup(popup);

    // Setup handlers
    popup.querySelector('#kh-qa-save-cancel').addEventListener('click', () => popup.remove());
    popup.querySelector('#kh-qa-save-confirm').addEventListener('click', async () => {
      const projectId = popup.querySelector('#kh-qa-save-project').value;
      const title = popup.querySelector('#kh-qa-save-title').value.trim();
      const saveContent = popup.querySelector('#kh-qa-save-content').value.trim();
      const tagsInput = popup.querySelector('#kh-qa-save-tags').value;
      const tags = tagsInput.split(',').map(t => t.trim()).filter(t => t);

      if (!projectId) {
        alert('Выберите проект');
        return;
      }

      try {
        await this.apiRequest('/api/knowledge/', 'POST', {
          project_id: projectId,
          title,
          content: saveContent,
          tags: [...tags, 'qa'],
          page_url: window.location.href,
          page_title: document.title
        });

        this.showNotification('Сохранено в базу знаний!', 'success');
        popup.remove();
      } catch (error) {
        this.showNotification(`Ошибка: ${error.message}`, 'error');
      }
    });

    // Close on outside click
    setTimeout(() => {
      document.addEventListener('click', (e) => {
        if (!popup.contains(e.target)) {
          popup.remove();
        }
      }, { once: true });
    }, 100);
  }

  centerPopup(popup) {
    // Center the popup on screen
    popup.style.position = 'fixed';
    popup.style.top = '50%';
    popup.style.left = '50%';
    popup.style.transform = 'translate(-50%, -50%)';
    popup.style.zIndex = '2147483647';
    
    // Store original centered state
    popup.dataset.isCentered = 'true';
  }

  makeDraggable(popup) {
    const header = popup.querySelector('.kh-qa-save-popup-header');
    let isDragging = false;
    let startX, startY, initialLeft, initialTop;

    header.addEventListener('mousedown', (e) => {
      isDragging = true;
      startX = e.clientX;
      startY = e.clientY;
      
      // Get current position - account for transform
      const rect = popup.getBoundingClientRect();
      
      // If popup is centered with transform, calculate actual position
      if (popup.dataset.isCentered === 'true') {
        initialLeft = rect.left;
        initialTop = rect.top;
        popup.style.transform = 'none';
        popup.dataset.isCentered = 'false';
      } else {
        initialLeft = parseFloat(popup.style.left) || rect.left;
        initialTop = parseFloat(popup.style.top) || rect.top;
      }
      
      popup.style.left = `${initialLeft}px`;
      popup.style.top = `${initialTop}px`;
      
      header.style.cursor = 'grabbing';
      header.style.userSelect = 'none';
      e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      
      let newLeft = initialLeft + dx;
      let newTop = initialTop + dy;
      
      // Constrain to viewport
      const popupRect = popup.getBoundingClientRect();
      const maxX = window.innerWidth - popupRect.width;
      const maxY = window.innerHeight - popupRect.height;
      
      newLeft = Math.max(0, Math.min(newLeft, maxX));
      newTop = Math.max(0, Math.min(newTop, maxY));
      
      popup.style.left = `${newLeft}px`;
      popup.style.top = `${newTop}px`;
    });

    document.addEventListener('mouseup', () => {
      if (isDragging) {
        isDragging = false;
        header.style.cursor = 'grab';
        header.style.userSelect = '';
      }
    });
  }

  // =========================================================================
  // Quick Popup (for text selection)
  // =========================================================================

  showQuickPopup(selection) {
    if (this.quickPopup) {
      this.quickPopup.remove();
    }

    this.quickPopup = document.createElement('div');
    this.quickPopup.className = 'kh-qa-quick-popup';
    this.quickPopup.innerHTML = `
      <div class="kh-qa-quick-popup-content">
        <div class="kh-qa-quick-popup-header">
          <span>❓ Вопрос по выделенному</span>
          <button class="kh-qa-quick-close">×</button>
        </div>
        <div class="kh-qa-selection-preview">
          "${this.escapeHtml(selection.slice(0, 100))}${selection.length > 100 ? '...' : ''}"
        </div>
        <textarea 
          class="kh-qa-quick-question" 
          placeholder="Что вас интересует?" 
          rows="2"
        ></textarea>
        <div class="kh-qa-quick-actions">
          <button class="kh-qa-btn kh-qa-btn-secondary kh-qa-quick-copy">Копировать</button>
          <button class="kh-qa-btn kh-qa-btn-primary kh-qa-quick-ask">
            <span>Задать</span>
            <span class="kh-qa-loading" style="display:none">⏳</span>
          </button>
        </div>
        <div class="kh-qa-quick-answer" style="display:none"></div>
      </div>
    `;

    document.body.appendChild(this.quickPopup);
    
    // Wait for render then position
    requestAnimationFrame(() => {
      this.positionQuickPopup();
    });
    
    this.setupQuickPopupHandlers(selection);
  }

  positionQuickPopup() {
    const selection = window.getSelection();
    if (!selection.rangeCount) return;

    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    const popupRect = this.quickPopup.getBoundingClientRect();

    // Calculate position - fixed positioning doesn't need scrollY
    let top = rect.bottom + 10;
    let left = rect.left + window.scrollX - 50;

    // Ensure popup stays within viewport
    if (top + popupRect.height > window.innerHeight) {
      // Show above selection if not enough space below
      top = rect.top - popupRect.height - 10;
    }
    top = Math.max(10, Math.min(top, window.innerHeight - popupRect.height - 10));

    if (left + popupRect.width > window.innerWidth) {
      // Align to right edge if too far right
      left = window.innerWidth - popupRect.width - 10;
    }
    left = Math.max(10, Math.min(left, window.innerWidth - popupRect.width - 10));

    this.quickPopup.style.position = 'fixed';
    this.quickPopup.style.top = `${top}px`;
    this.quickPopup.style.left = `${left}px`;
    this.quickPopup.style.zIndex = '2147483647';
  }

  setupQuickPopupHandlers(selection) {
    const popup = this.quickPopup;

    // Close button
    popup.querySelector('.kh-qa-quick-close').addEventListener('click', () => {
      popup.remove();
      this.quickPopup = null;
    });

    // Copy button
    popup.querySelector('.kh-qa-quick-copy').addEventListener('click', () => {
      navigator.clipboard.writeText(selection);
      this.showNotification('Скопировано!', 'success');
    });

    // Ask button
    popup.querySelector('.kh-qa-quick-ask').addEventListener('click', async () => {
      const questionInput = popup.querySelector('.kh-qa-quick-question');
      const question = questionInput.value.trim() || 'Объясни это';
      const askBtn = popup.querySelector('.kh-qa-quick-ask');
      const loadingIndicator = askBtn.querySelector('.kh-qa-loading');
      const answerContainer = popup.querySelector('.kh-qa-quick-answer');

      askBtn.disabled = true;
      loadingIndicator.style.display = 'inline';

      try {
        const response = await this.apiRequest('/api/qa/', 'POST', {
          question: question,
          context: selection,
          max_context: 3
        });

        answerContainer.innerHTML = `
          <div class="kh-qa-answer-content">
            <strong>Ответ:</strong>
            <p>${this.escapeHtml(response.answer)}</p>
          </div>
          <div class="kh-qa-answer-actions">
            <button class="kh-qa-btn kh-qa-btn-secondary kh-qa-answer-copy">Копировать</button>
            <button class="kh-qa-btn kh-qa-btn-primary kh-qa-answer-save">Сохранить</button>
          </div>
        `;
        answerContainer.style.display = 'block';

        // Copy answer
        answerContainer.querySelector('.kh-qa-answer-copy').addEventListener('click', () => {
          navigator.clipboard.writeText(response.answer);
          this.showNotification('Ответ скопирован!', 'success');
        });

        // Save answer
        answerContainer.querySelector('.kh-qa-answer-save').addEventListener('click', () => {
          this.saveToKnowledgeBase(response.answer, response.sources);
          popup.remove();
          this.quickPopup = null;
        });

      } catch (error) {
        answerContainer.innerHTML = `<p class="kh-qa-error">Ошибка: ${error.message}</p>`;
        answerContainer.style.display = 'block';
      } finally {
        askBtn.disabled = false;
        loadingIndicator.style.display = 'none';
      }
    });

    // Close on outside click
    setTimeout(() => {
      document.addEventListener('click', (e) => {
        if (!popup.contains(e.target)) {
          popup.remove();
          this.quickPopup = null;
        }
      }, { once: true });
    }, 100);
  }

  // =========================================================================
  // Utility Methods
  // =========================================================================

  async apiRequest(endpoint, method = 'GET', data = null) {
    return new Promise((resolve, reject) => {
      chrome.runtime.sendMessage(
        { type: 'CONTENT_API_REQUEST', endpoint, method, data },
        response => {
          if (response && response.success) {
            resolve(response.data);
          } else {
            reject(new Error(response?.error || 'Request failed'));
          }
        }
      );
    });
  }

  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `kh-notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
  }
}

// Initialize Q&A functionality
const knowledgeHelperQA = new KnowledgeHelperQA();
console.log('[Knowledge Helper Q&A] Initialized');
