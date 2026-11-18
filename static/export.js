const form = document.getElementById('export-form');
const metaToken = document.querySelector('meta[name="app-token"]');
const logoutBtn = document.getElementById('logout-btn');

let currentToken = metaToken ? metaToken.content : null;

console.log('✅ Export page loaded');
console.log('📋 Token:', currentToken ? 'Set' : 'NOT SET');

async function loadProjects() {
  console.log('📦 Loading projects...');
  try {
    const response = await fetch('/api/projects', {
      headers: { 'X-App-Token': currentToken }
    });
    if (!response.ok) throw new Error('Failed to load projects');
    const data = await response.json();
    console.log('✅ Projects loaded:', data.projects.length);
    
    const projectList = document.getElementById('project-list');
    projectList.innerHTML = '';
    data.projects.forEach(project => {
      const label = document.createElement('label');
      label.className = 'checkbox-label';
      label.innerHTML = `
        <input type="checkbox" name="projects" value="${project.key}">
        <span>${project.name} (${project.key})</span>
      `;
      const checkbox = label.querySelector('input[type="checkbox"]');
      checkbox.addEventListener('change', loadStatuses);
      projectList.appendChild(label);
    });
  } catch (error) {
    console.error('❌ Error loading projects:', error.message);
    document.getElementById('project-error').textContent = error.message;
    document.getElementById('project-error').style.display = 'block';
  }
}

async function loadFields() {
  console.log('📋 Loading fields...');
  try {
    const response = await fetch('/api/fields', {
      headers: { 'X-App-Token': currentToken }
    });
    if (!response.ok) throw new Error('Failed to load fields');
    const data = await response.json();
    console.log('✅ Fields loaded. Standard:', Object.keys(data.standard).length, 'Custom:', data.custom.length);

    const selectedFields = document.getElementById('selected-fields');
    const customFields = document.getElementById('custom-fields');
    const customFieldsSearch = document.getElementById('custom-fields-search');
    
    // Store standard field names
    const standardFieldMap = {
      'key': 'Issue key',
      'summary': 'Summary',
      'assignee': 'Assignee',
      'status': 'Status',
      'created': 'Created'
    };
    
    const allCustomFields = new Map();
    data.custom.forEach(([id, name]) => {
      allCustomFields.set(name, { id, name });
    });

    // Render selected fields (standard fields - always there)
    function renderSelectedFields() {
      selectedFields.innerHTML = '';
      
      // Add standard fields
      Object.entries(standardFieldMap).forEach(([key, name]) => {
        const label = document.createElement('label');
        label.className = 'checkbox-label standard-field';
        label.innerHTML = `
          <input type="checkbox" name="columns" value="${name}" checked disabled>
          <span>${name}</span>
        `;
        selectedFields.appendChild(label);
      });
      
      // Add selected custom fields
      Array.from(document.querySelectorAll('#custom-fields input[type="checkbox"]:checked')).forEach(checkbox => {
        const fieldName = checkbox.value;
        const label = document.createElement('label');
        label.className = 'checkbox-label';
        label.innerHTML = `
          <input type="checkbox" name="columns" value="${fieldName}" checked data-custom-field="true">
          <span>${fieldName}</span>
        `;
        const newCheckbox = label.querySelector('input[type="checkbox"]');
        newCheckbox.addEventListener('change', (e) => {
          if (!e.target.checked) {
            // Uncheck from available fields
            const availableCheckbox = document.querySelector(`#custom-fields input[value="${fieldName}"]`);
            if (availableCheckbox) {
              availableCheckbox.checked = false;
            }
            renderAvailableFields();
            renderSelectedFields();
          }
        });
        selectedFields.appendChild(label);
      });
    }

    // Render available custom fields (with search)
    function renderAvailableFields() {
      customFields.innerHTML = '';
      const searchTerm = customFieldsSearch.value.toLowerCase();
      
      allCustomFields.forEach((field, name) => {
        const isSelected = document.querySelector(`#custom-fields input[value="${name}"]:checked`);
        const matches = searchTerm === '' || name.toLowerCase().includes(searchTerm);
        
        if (!isSelected && matches) {
          const label = document.createElement('label');
          label.className = 'checkbox-label custom-field-option';
          label.setAttribute('data-field-name', name.toLowerCase());
          label.innerHTML = `
            <input type="checkbox" name="columns" value="${name}">
            <span>${name}</span>
          `;
          const checkbox = label.querySelector('input[type="checkbox"]');
          checkbox.addEventListener('change', () => {
            renderSelectedFields();
            renderAvailableFields();
          });
          customFields.appendChild(label);
        }
      });
    }

    // Search functionality
    customFieldsSearch.addEventListener('input', () => {
      renderAvailableFields();
    });

    // Initial render
    renderAvailableFields();
    renderSelectedFields();

  } catch (error) {
    console.error('❌ Error loading fields:', error.message);
    document.getElementById('column-error').textContent = error.message;
    document.getElementById('column-error').style.display = 'block';
  }
}

async function loadStatuses() {
  console.log('📊 Loading statuses...');
  try {
    const selectedProjects = Array.from(document.querySelectorAll('input[name="projects"]:checked'))
      .map(el => el.value);
    
    if (selectedProjects.length === 0) {
      console.log('ℹ️  No projects selected, clearing statuses');
      document.getElementById('status-list').innerHTML = '';
      return;
    }

    console.log('📦 Fetching statuses for projects:', selectedProjects);
    const statusSet = new Set();

    // Fetch statuses for all selected projects
    for (const projectKey of selectedProjects) {
      try {
        const response = await fetch(`/api/statuses?project=${projectKey}`, {
          headers: { 'X-App-Token': currentToken }
        });
        if (response.ok) {
          const data = await response.json();
          data.statuses.forEach(status => statusSet.add(status));
          console.log(`✅ Statuses for ${projectKey}:`, data.statuses);
        } else {
          console.warn(`⚠️  Could not load statuses for ${projectKey}`);
        }
      } catch (error) {
        console.warn(`⚠️  Error loading statuses for ${projectKey}:`, error.message);
      }
    }

    // Display statuses
    const statusList = document.getElementById('status-list');
    statusList.innerHTML = '';
    
    if (statusSet.size === 0) {
      console.log('ℹ️  No statuses found');
      statusList.innerHTML = '<p style="color: #999; font-size: 14px;">No statuses available</p>';
      return;
    }

    Array.from(statusSet).sort().forEach(status => {
      const label = document.createElement('label');
      label.className = 'checkbox-label';
      label.innerHTML = `
        <input type="checkbox" name="statuses" value="${status}">
        <span>${status}</span>
      `;
      statusList.appendChild(label);
    });
    console.log('✅ Statuses displayed:', statusSet.size);
  } catch (error) {
    console.error('❌ Error loading statuses:', error.message);
    document.getElementById('status-error').textContent = error.message;
    document.getElementById('status-error').style.display = 'block';
  }
}

function setDefaultDates() {
  const today = new Date();
  const monthAgo = new Date(today.getFullYear(), today.getMonth() - 1, today.getDate());
  document.getElementById('start-date').value = monthAgo.toISOString().split('T')[0];
  document.getElementById('end-date').value = today.toISOString().split('T')[0];
  console.log('📅 Date range set');
}

if (form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    console.log('📤 Form submitted');

    const projects = Array.from(document.querySelectorAll('input[name="projects"]:checked'))
      .map(el => el.value);
    const columns = Array.from(document.querySelectorAll('input[name="columns"]:checked'))
      .map(el => el.value);
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;

    console.log('📊 Export params:', { projects, columns, startDate, endDate });

    if (!projects.length || !columns.length) {
      document.getElementById('form-error').textContent = 'Please select at least one project and one column';
      document.getElementById('form-error').style.display = 'block';
      return;
    }

    try {
      document.getElementById('form-error').style.display = 'none';
      const submitBtn = form.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Exporting...';

      const response = await fetch('/api/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-App-Token': currentToken
        },
        body: JSON.stringify({
          projects,
          columns,
          start_date: startDate,
          end_date: endDate,
          statuses: Array.from(document.querySelectorAll('input[name="statuses"]:checked')).map(el => el.value)
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Export failed');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `jira_export_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      submitBtn.disabled = false;
      submitBtn.textContent = 'Export to Excel';
      console.log('✅ Export successful');
    } catch (error) {
      console.error('❌ Export error:', error.message);
      document.getElementById('form-error').textContent = error.message;
      document.getElementById('form-error').style.display = 'block';
      form.querySelector('button[type="submit"]').disabled = false;
      form.querySelector('button[type="submit"]').textContent = 'Export to Excel';
    }
  });
} else {
  console.error('❌ Export form not found!');
}

if (logoutBtn) {
  logoutBtn.addEventListener('click', async () => {
    if (confirm('Disconnect from Jira?')) {
      try {
        await fetch('/api/logout', {
          method: 'POST',
          headers: { 'X-App-Token': currentToken }
        });
        window.location.href = '/';
      } catch (error) {
        alert('Logout failed');
      }
    }
  });
}

// Load data on page initialization
console.log('🚀 Initializing export page...');
loadProjects();
loadFields();
setDefaultDates();
