// Knowledge Helper - Popup Script
const SERVER_URL = 'http://127.0.0.1:8000';

// State
let projects = [];
let currentTab = 'save';

// Init
document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  checkServerStatus();
  loadProjects();
  initSaveTab();
  initSearchTab();
  initQaTab();
  initGraphTab();
});

// Tab Navigation
function initTabs() {
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const tabName = tab.dataset.tab;
      switchTab(tabName);
    });
  });
}

function switchTab(tabName) {
  currentTab = tabName;
  
  // Update tab buttons
  document.querySelectorAll('.tab').forEach(t => {
    t.classList.toggle('active', t.dataset.tab === tabName);
  });
  
  // Update tab content
  document.querySelectorAll('.tab-content').forEach(c => {
    c.classList.toggle('active', c.id === `tab-${tabName}`);
  });
}

// Server Status
async function checkServerStatus() {
  const dot = document.getElementById('status-dot');
  const text = document.getElementById('status-text');
  
  try {
    const response = await fetch(`${SERVER_URL}/health`);
    if (response.ok) {
      dot.classList.add('connected');
      text.textContent = 'Connected to server';
    } else {
      throw new Error('Server error');
    }
  } catch (error) {
    dot.classList.remove('connected');
    text.textContent = 'Server not available';
  }
}

// Load Projects
async function loadProjects() {
  try {
    const response = await fetch(`${SERVER_URL}/api/projects/`);
    projects = await response.json();
    
    // Update project selects
    const saveSelect = document.getElementById('save-project');
    const graphSelect = document.getElementById('graph-project');
    
    const optionsHtml = projects.length
      ? projects.map(p => `<option value="${p.id}">${p.name}</option>`).join('')
      : '<option value="">No projects</option>';
    
    saveSelect.innerHTML = optionsHtml;
    graphSelect.innerHTML = '<option value="">All Projects</option>' + optionsHtml;
  } catch (error) {
    console.error('Failed to load projects:', error);
  }
}

// Save Tab
function initSaveTab() {
  document.getElementById('save-btn').addEventListener('click', saveEntry);
  
  // New project form handlers
  document.getElementById('new-project-btn').addEventListener('click', showNewProjectForm);
  document.getElementById('create-project-btn').addEventListener('click', createProject);
  document.getElementById('cancel-project-btn').addEventListener('click', hideNewProjectForm);
  
  // Enter key in project name input
  document.getElementById('new-project-name').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') createProject();
  });
  
  // Try to get current tab info
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) {
      document.getElementById('save-title').value = tabs[0].title || '';
    }
  });
}

function showNewProjectForm() {
  document.getElementById('new-project-form').style.display = 'block';
  document.getElementById('new-project-name').focus();
}

function hideNewProjectForm() {
  document.getElementById('new-project-form').style.display = 'none';
  document.getElementById('new-project-name').value = '';
}

async function createProject() {
  const name = document.getElementById('new-project-name').value.trim();
  if (!name) {
    alert('Please enter project name');
    return;
  }
  
  try {
    const response = await fetch(`${SERVER_URL}/api/projects/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description: '' })
    });
    
    if (!response.ok) throw new Error('Failed');
    
    const project = await response.json();
    
    // Reload projects and select new one
    await loadProjects();
    document.getElementById('save-project').value = project.id;
    
    hideNewProjectForm();
  } catch (error) {
    console.error('Create project error:', error);
    alert('Failed to create project');
  }
}

async function saveEntry() {
  const projectId = document.getElementById('save-project').value;
  const title = document.getElementById('save-title').value.trim();
  const content = document.getElementById('save-content').value.trim();
  const tagsInput = document.getElementById('save-tags').value.trim();
  const tags = tagsInput ? tagsInput.split(',').map(t => t.trim()).filter(t => t) : [];

  if (!projectId) {
    alert('Please select a project');
    return;
  }
  if (!title) {
    alert('Please enter a title');
    return;
  }
  if (!content) {
    alert('Please enter content');
    return;
  }

  const btn = document.getElementById('save-btn');
  btn.disabled = true;
  btn.textContent = 'Saving...';

  try {
    // Get current tab URL
    let pageUrl = '';
    let pageTitle = '';
    chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
      if (tabs[0]) {
        pageUrl = tabs[0].url || '';
        pageTitle = tabs[0].title || '';
      }

      const response = await fetch(`${SERVER_URL}/api/knowledge/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectId,
          title,
          content,
          page_url: pageUrl,
          page_title: pageTitle,
          tags
        })
      });

      if (!response.ok) throw new Error('Failed to save');

      btn.textContent = 'Saved! ✅';
      setTimeout(() => {
        btn.textContent = 'Save Entry';
        btn.disabled = false;
        document.getElementById('save-title').value = '';
        document.getElementById('save-content').value = '';
        document.getElementById('save-tags').value = '';
      }, 2000);
    });
  } catch (error) {
    console.error('Save error:', error);
    btn.textContent = 'Error - Try Again';
    btn.disabled = false;
  }
}

// Search Tab
function initSearchTab() {
  const input = document.getElementById('search-input');
  let debounceTimer;
  
  input.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(search, 300);
  });
  
  input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      clearTimeout(debounceTimer);
      search();
    }
  });
}

async function search() {
  const query = document.getElementById('search-input').value.trim();
  const resultsDiv = document.getElementById('search-results');
  
  if (!query) {
    resultsDiv.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">🔍</div>
        <p>Search your knowledge base</p>
      </div>
    `;
    return;
  }

  try {
    const response = await fetch(`${SERVER_URL}/api/knowledge/unified/${encodeURIComponent(query)}`);
    const results = await response.json();
    
    if (results.length === 0) {
      resultsDiv.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">📭</div>
          <p>No results found</p>
        </div>
      `;
      return;
    }

    resultsDiv.innerHTML = results.map(item => `
      <div class="result-item">
        <h4>${escapeHtml(item.title)}</h4>
        <p>${escapeHtml(item.snippet)}</p>
        <div class="result-tags">
          ${item.tags.map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('')}
        </div>
      </div>
    `).join('');
  } catch (error) {
    console.error('Search error:', error);
    resultsDiv.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">❌</div>
        <p>Search failed</p>
      </div>
    `;
  }
}

// Q&A Tab
function initQaTab() {
  document.getElementById('qa-btn').addEventListener('click', askQuestion);
  document.getElementById('qa-question').addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      askQuestion();
    }
  });
}

async function askQuestion() {
  const question = document.getElementById('qa-question').value.trim();
  const answerDiv = document.getElementById('qa-answer');
  
  if (!question) return;

  const btn = document.getElementById('qa-btn');
  btn.disabled = true;
  btn.textContent = 'Thinking...';

  try {
    const response = await fetch(`${SERVER_URL}/api/qa/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });

    if (!response.ok) throw new Error('Failed');

    const data = await response.json();
    
    answerDiv.style.display = 'block';
    answerDiv.innerHTML = `
      <div class="qa-answer">
        <h4>Answer (${data.model})</h4>
        <p>${escapeHtml(data.answer).replace(/\n/g, '<br>')}</p>
        ${data.sources.length ? `
          <div class="qa-sources">
            <h5>Sources:</h5>
            <div class="result-tags">
              ${data.sources.map(s => `<span class="tag">${escapeHtml(s.title)}</span>`).join('')}
            </div>
          </div>
        ` : ''}
      </div>
    `;
  } catch (error) {
    console.error('Q&A error:', error);
    answerDiv.style.display = 'block';
    answerDiv.innerHTML = `
      <div class="qa-answer">
        <p style="color: #ef4444;">Failed to get answer. Check your LLM API key.</p>
      </div>
    `;
  }

  btn.disabled = false;
  btn.textContent = 'Ask';
}

// Graph Tab
function initGraphTab() {
  document.getElementById('graph-btn').addEventListener('click', openGraphView);
  document.getElementById('graph-download').addEventListener('click', downloadGraph);
}

async function openGraphView() {
  const projectId = document.getElementById('graph-project').value;
  const url = chrome.runtime.getURL('graph/graph.html');
  
  // Store project ID for graph page
  chrome.storage.local.set({ graphProjectId: projectId }, () => {
    chrome.tabs.create({ url });
  });
}

async function downloadGraph() {
  const projectId = document.getElementById('graph-project').value;
  
  try {
    const url = `${SERVER_URL}/api/graph/${projectId ? `?project_id=${projectId}` : ''}`;
    const response = await fetch(url);
    const data = await response.json();
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const downloadUrl = URL.createObjectURL(blob);
    
    chrome.downloads.download({
      url: downloadUrl,
      filename: 'knowledge-graph.json'
    });
  } catch (error) {
    console.error('Download error:', error);
    alert('Failed to download graph');
  }
}

// Utility
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
