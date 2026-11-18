const form = document.getElementById('login-form');
const errorMessage = document.getElementById('error-message');
const metaToken = document.querySelector('meta[name="app-token"]');

let currentToken = metaToken ? metaToken.content : null;

console.log('✅ Login page loaded');
console.log('📋 Initial token:', currentToken ? 'Set' : 'NOT SET');

// Ensure form exists before attaching event listener
if (form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    console.log('🔵 Form submit event triggered');
    errorMessage.style.display = 'none';

    // Get fresh token before submitting
    console.log('🔄 Fetching fresh token...');
    try {
      const tokenResponse = await fetch('/api/token');
      if (tokenResponse.ok) {
        const tokenData = await tokenResponse.json();
        currentToken = tokenData.token;
        console.log('✅ Fresh token obtained:', currentToken.slice(0, 10) + '...');
      } else {
        console.warn('⚠️  Could not fetch fresh token, using initial token');
      }
    } catch (err) {
      console.warn('⚠️  Token fetch error (continuing with current):', err.message);
    }

    const baseUrl = document.getElementById('base-url').value.trim();
    const email = document.getElementById('email').value.trim();
    const apiToken = document.getElementById('api-token').value.trim();

    console.log('📝 Form values:', { baseUrl, email, apiToken: '***' });

    if (!baseUrl || !email || !apiToken) {
      console.error('❌ Missing required fields');
      errorMessage.textContent = 'All fields are required.';
      errorMessage.style.display = 'block';
      return;
    }

    try {
      console.log('📡 Sending POST request to /api/connect');
      const response = await fetch('/api/connect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-App-Token': currentToken
        },
        body: JSON.stringify({
          base_url: baseUrl,
          email: email,
          api_token: apiToken
        })
      });

      console.log('📦 Response status:', response.status);
      
      let data = {};
      try {
        data = await response.json();
      } catch (e) {
        console.warn('⚠️  Could not parse response as JSON');
        data = { error: 'Server error. Please try again.' };
      }

      if (response.status === 403) {
        console.error('❌ Token error (403):', data.error);
        errorMessage.textContent = data.error || 'Session expired. Please refresh the page.';
        errorMessage.style.display = 'block';
        return;
      }

      if (!response.ok) {
        console.error('❌ Response not OK:', data);
        throw new Error(data.error || 'Connection failed');
      }

      console.log('✅ Connection successful! Redirecting...');
      window.location.href = '/';
    } catch (error) {
      console.error('❌ Error caught:', error.message);
      errorMessage.textContent = error.message;
      errorMessage.style.display = 'block';
    }
  });
} else {
  console.error('❌ Login form not found!');
}
