// Knowledge Helper - Content Script
// Handles text selection and inline save popup
// All API calls go through background script via chrome.runtime.sendMessage

class KnowledgeHelperContent {
  constructor() {
    this.popup = null;
    this.projects = [];
    this.selectedText = '';
    this.init();
  }

  init() {
    chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
      if (msg.type === 'SHOW_SAVE_POPUP') {
        this.showSavePopup(msg.data);
      }
      return true;
    });

    document.addEventListener('mouseup', () => {
      const selection = window.getSelection().toString().trim();
      if (selection) {
        this.selectedText = selection;
      }
    });
  }

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

  async showSavePopup(contextData = {}) {
    if (this.popup) {
      this.popup.remove();
    }

    const escapedTitle = this.escapeHtml(contextData.title || document.title);
    const escapedSelection = this.escapeHtml(contextData.selection || '');
    
    this.popup = document.createElement('div');
    this.popup.className = 'kh-container';
    this.popup.innerHTML = `
      <div class="kh-popup">
        <div class="kh-header">
          <h3>📚 Save to Knowledge Base</h3>
          <button class="kh-close">&times;</button>
        </div>
        <div class="kh-body">
          <div class="kh-selection-info" id="selection-preview" style="display: ${contextData.selection ? 'block' : 'none'};">
            <strong>Selected:</strong> <span id="selection-text">${escapedSelection.substring(0, 100)}${contextData.selection && contextData.selection.length > 100 ? '...' : ''}</span>
          </div>
          <div class="kh-form-group">
            <label>Project</label>
            <select id="kh-project">
              <option value="">Loading projects...</option>
            </select>
          </div>
          <div class="kh-form-group">
            <label>Title</label>
            <input type="text" id="kh-title" placeholder="Enter title..." value="${escapedTitle}">
          </div>
          <div class="kh-form-group">
            <label>Content</label>
            <textarea id="kh-content" placeholder="Enter or paste content...">${escapedSelection}</textarea>
          </div>
          <div class="kh-form-group">
            <label>Tags (comma separated)</label>
            <div class="kh-tags-input" id="kh-tags-container">
              <input type="text" class="kh-tag-input" id="kh-tag-input" placeholder="Add tags...">
            </div>
          </div>
          <div class="kh-actions">
            <button class="kh-btn kh-btn-secondary" id="kh-cancel">Cancel</button>
            <button class="kh-btn kh-btn-primary" id="kh-save">Save</button>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(this.popup);
    await this.loadProjects();
    this.setupEventHandlers();
  }

  async loadProjects() {
    try {
      const projects = await this.apiRequest('/api/projects/');
      this.projects = projects;

      const select = this.popup.querySelector('#kh-project');
      select.innerHTML = projects.length 
        ? projects.map(p => `<option value="${p.id}">${this.escapeHtml(p.name)}</option>`).join('')
        : '<option value="">No projects - create one first</option>';
    } catch (error) {
      console.error('Failed to load projects:', error);
      this.popup.querySelector('#kh-project').innerHTML = '<option value="">Server not available</option>';
      this.showNotification('Cannot connect to server: ' + error.message, 'error');
    }
  }

  setupEventHandlers() {
    this.popup.querySelector('.kh-close').addEventListener('click', () => {
      this.popup.remove();
      this.popup = null;
    });

    this.popup.querySelector('#kh-cancel').addEventListener('click', () => {
      this.popup.remove();
      this.popup = null;
    });

    this.popup.querySelector('#kh-save').addEventListener('click', () => this.saveEntry());

    const tagInput = this.popup.querySelector('#kh-tag-input');
    tagInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ',') {
        e.preventDefault();
        this.addTag(tagInput.value.trim().replace(',', ''));
        tagInput.value = '';
      }
    });

    setTimeout(() => {
      document.addEventListener('click', (e) => {
        if (this.popup && !this.popup.contains(e.target)) {
          this.popup.remove();
          this.popup = null;
        }
      }, { once: true });
    }, 100);
  }

  addTag(tag) {
    if (!tag) return;
    
    const container = this.popup.querySelector('#kh-tags-container');
    const input = this.popup.querySelector('#kh-tag-input');
    
    const tagEl = document.createElement('span');
    tagEl.className = 'kh-tag';
    tagEl.innerHTML = `${this.escapeHtml(tag)}<span class="kh-tag-remove">&times;</span>`;
    
    tagEl.querySelector('.kh-tag-remove').addEventListener('click', () => tagEl.remove());
    
    container.insertBefore(tagEl, input);
  }

  getTags() {
    const tags = [];
    this.popup.querySelectorAll('.kh-tag').forEach(tagEl => {
      const text = tagEl.textContent.replace('×', '').trim();
      if (text) tags.push(text);
    });
    return tags;
  }

  async saveEntry() {
    const projectId = this.popup.querySelector('#kh-project').value;
    const title = this.popup.querySelector('#kh-title').value.trim();
    const content = this.popup.querySelector('#kh-content').value.trim();
    const tags = this.getTags();

    if (!projectId) {
      this.showNotification('Please select a project', 'error');
      return;
    }
    if (!title) {
      this.showNotification('Please enter a title', 'error');
      return;
    }
    if (!content) {
      this.showNotification('Please enter content', 'error');
      return;
    }

    const saveBtn = this.popup.querySelector('#kh-save');
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';

    try {
      await this.apiRequest('/api/knowledge/', 'POST', {
        project_id: projectId,
        title,
        content,
        page_url: window.location.href,
        page_title: document.title,
        selection: this.selectedText || null,
        tags
      });

      this.showNotification('Saved successfully!', 'success');
      this.popup.remove();
      this.popup = null;
    } catch (error) {
      console.error('Save error:', error);
      this.showNotification('Failed to save: ' + error.message, 'error');
      saveBtn.disabled = false;
      saveBtn.textContent = 'Save';
    }
  }

  showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `kh-notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

const knowledgeHelper = new KnowledgeHelperContent();
