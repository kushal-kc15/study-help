(function () {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
  const socket = new WebSocket(wsProtocol + window.location.host + '/ws/presence/');

  function applyOnlineStatus(onlineUsers) {
    // update all [data-user-id] elements with an .online-dot child
    document.querySelectorAll('[data-user-id]').forEach(el => {
      const uid = parseInt(el.dataset.userId);
      const dot = el.querySelector('.online-dot');
      if (dot) {
        dot.classList.toggle('online-dot--active', onlineUsers.includes(uid));
      }
    });
  }

  socket.onmessage = function (e) {
    const data = JSON.parse(e.data);
    if (data.online_users) applyOnlineStatus(data.online_users);
  };

  // Also poll every 30s so dots stay accurate when others join/leave
  setInterval(function () {
    fetch('/online-status/')
      .then(r => r.json())
      .then(data => applyOnlineStatus(data.online_users));
  }, 30000);
})();
