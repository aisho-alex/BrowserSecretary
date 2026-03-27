// Knowledge Graph - Main Script
const SERVER_URL = 'http://127.0.0.1:8000';
let network = null;
let nodes = null;
let edges = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  loadProjects();
  initNetwork();
  loadGraph();
});

async function loadProjects() {
  try {
    const response = await fetch(`${SERVER_URL}/api/projects/`);
    const projects = await response.json();

    const select = document.getElementById('project-select');
    projects.forEach(p => {
      const option = document.createElement('option');
      option.value = p.id;
      option.textContent = p.name;
      select.appendChild(option);
    });
  } catch (error) {
    console.error('Failed to load projects:', error);
  }
}

function initNetwork() {
  const container = document.getElementById('graph-container');

  nodes = new vis.DataSet([]);
  edges = new vis.DataSet([]);

  const data = { nodes, edges };

  const options = {
    nodes: {
      shape: 'dot',
      size: 20,
      font: {
        size: 14,
        color: '#ffffff'
      },
      borderWidth: 2,
      shadow: true
    },
    edges: {
      width: 2,
      color: { color: '#667eea', highlight: '#764ba2' },
      arrows: { to: { enabled: true, scaleFactor: 0.5 } },
      smooth: { type: 'continuous' }
    },
    physics: {
      stabilization: { iterations: 200 },
      barnesHut: {
        gravitationalConstant: -2000,
        springConstant: 0.04
      }
    },
    interaction: {
      hover: true,
      tooltipDelay: 200
    }
  };

  network = new vis.Network(container, data, options);

  // Node click handler
  network.on('click', (params) => {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0];
      showNodeInfo(nodeId);
    } else {
      hideNodeInfo();
    }
  });
}

async function loadGraph() {
  document.getElementById('loading').style.display = 'block';

  const projectId = document.getElementById('project-select').value;
  const url = `${SERVER_URL}/api/graph/${projectId ? `?project_id=${projectId}` : ''}`;

  try {
    const response = await fetch(url);
    const graphData = await response.json();

    // Clear existing data
    nodes.clear();
    edges.clear();

    // Add nodes with colors based on tags
    const nodeData = graphData.nodes.map((n, i) => ({
      id: n.id,
      label: n.label,
      title: n.title,
      tags: n.tags,
      color: getNodeColor(n.tags),
      x: Math.cos(i / graphData.nodes.length * 2 * Math.PI) * 300,
      y: Math.sin(i / graphData.nodes.length * 2 * Math.PI) * 300
    }));

    nodes.add(nodeData);

    // Add edges
    const edgeData = graphData.edges.map(e => ({
      from: e.source,
      to: e.target,
      label: e.type,
      value: e.weight
    }));

    edges.add(edgeData);

    // Update stats
    document.getElementById('node-count').textContent = graphData.nodes.length;
    document.getElementById('edge-count').textContent = graphData.edges.length;

  } catch (error) {
    console.error('Failed to load graph:', error);
  }

  document.getElementById('loading').style.display = 'none';
}

function getNodeColor(tags) {
  const colors = {
    'api': '#10b981',
    'docs': '#3b82f6',
    'code': '#8b5cf6',
    'design': '#ec4899',
    'bug': '#ef4444',
    'feature': '#f59e0b'
  };

  if (tags && tags.length > 0) {
    const tag = tags[0].toLowerCase();
    return colors[tag] || '#667eea';
  }
  return '#667eea';
}

function showNodeInfo(nodeId) {
  const node = nodes.get(nodeId);
  if (!node) return;

  document.getElementById('node-title').textContent = node.title;
  document.getElementById('node-content').textContent = node.label;

  const tagsDiv = document.getElementById('node-tags');
  tagsDiv.innerHTML = (node.tags || [])
    .map(t => `<span class="tag">${t}</span>`)
    .join('');

  document.getElementById('node-info').style.display = 'block';
}

function hideNodeInfo() {
  document.getElementById('node-info').style.display = 'none';
}

// Event handlers
document.getElementById('project-select').addEventListener('change', loadGraph);
document.getElementById('refresh-btn').addEventListener('click', loadGraph);
document.getElementById('download-btn').addEventListener('click', downloadGraph);

async function downloadGraph() {
  const projectId = document.getElementById('project-select').value;
  const url = `${SERVER_URL}/api/graph/${projectId ? `?project_id=${projectId}` : ''}`;

  try {
    const response = await fetch(url);
    const data = await response.json();

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const downloadUrl = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = 'knowledge-graph.json';
    a.click();
  } catch (error) {
    console.error('Download failed:', error);
  }
}
