/* CivicSetu — Main JS */

// Auto-dismiss alerts after 5s
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.cs-alert').forEach(el => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });

  // Navbar active link highlight
  const path = window.location.pathname;
  document.querySelectorAll('.cs-navlink').forEach(link => {
    if (link.getAttribute('href') && path.startsWith(link.getAttribute('href'))) {
      link.style.color = 'var(--cs-text)';
      link.style.background = 'rgba(91,142,255,0.12)';
    }
  });
});

// Toggle password field visibility
function togglePass(fid, iid) {
  const f = document.getElementById(fid);
  const i = document.getElementById(iid);
  if (!f) return;
  const isPass = f.type === 'password';
  f.type = isPass ? 'text' : 'password';
  if (i) {
    i.className = isPass ? 'bi bi-eye-slash' : 'bi bi-eye';
  }
}
