// frontend/js/server_select_app.js
const serverBtns = document.querySelectorAll('.server-btn');

serverBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
        // 1. 視覺標記
        serverBtns.forEach(b => b.classList.remove('selected'));
        e.target.classList.add('selected');

        // 2. 儲存選擇
        const server_id = e.target.getAttribute('data-server-id');
        localStorage.setItem('selected_server_id', server_id);

        console.log(`已選擇伺服器: ${server_id}，準備進入大廳...`);
        
        // 3. 跳轉到大廳
        alert(`已選擇 ${server_id}，請點擊確認進入大廳！`); // 測試用 alert
        window.location.href = 'lobby.html';
    });
});