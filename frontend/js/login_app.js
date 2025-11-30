// frontend/js/login_app.js (最終正確版)

import { login, register } from './api_client.js';

const form = document.getElementById('auth-form');
const loginBtn = document.getElementById('login-btn');
const registerGroup = document.getElementById('display-name-group');
let isRegisterMode = false;

// 1. 處理登入/註冊模式切換
document.getElementById('switch-to-register-btn').addEventListener('click', () => {
    isRegisterMode = !isRegisterMode;
    if (isRegisterMode) {
        loginBtn.textContent = '註冊';
        registerGroup.style.display = 'block';
        document.getElementById('switch-to-register-btn').textContent = '切換至登入';
    } else {
        loginBtn.textContent = '登入';
        registerGroup.style.display = 'none';
        document.getElementById('switch-to-register-btn').textContent = '切換至註冊';
    }
});

// 2. 處理表單提交 (登入/註冊 - 串接 API)
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const messageArea = document.getElementById('message-area');
    messageArea.textContent = '處理中...';
    
    // 這裡不再需要檢查 selected_server_id！
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const displayName = document.getElementById('display-name').value;
    
    // =========================================================
    // ⚠️ 這裡是模擬成功區塊，當組員A完成後，請刪除這整個 if 判斷 ⚠️
    // =========================================================
    if (username === "test" && password === "123") {
        messageArea.textContent = '✅ 模擬登入成功！正在導向伺服器選擇...';

        // 模擬後端回傳的關鍵資訊
        const responseData = {
            token: 'MOCK_TOKEN_FOR_TESTING',
            user_id: 100,
            display_name: '測試玩家'
        };

        localStorage.setItem('user_token', responseData.token);
        localStorage.setItem('user_id', responseData.user_id); 
        localStorage.setItem('display_name', responseData.display_name);
        
        // 延遲一下跳轉，讓你看見成功的訊息
        await new Promise(resolve => setTimeout(resolve, 500)); 
        window.location.href = 'server-select.html';
        return; 
    }
    // =========================================================
    // ⚠️ 模擬區塊結束 ⚠️
    // =========================================================


    try {
        let responseData;

        if (isRegisterMode) {
            // 呼叫註冊 API，不傳 server_id
            responseData = await register(username, password, displayName);
            messageArea.textContent = '✅ 註冊成功！正在導向伺服器選擇...';
        } else {
            // 呼叫登入 API，不傳 server_id
            responseData = await login(username, password);
            messageArea.textContent = '✅ 登入成功！正在導向伺服器選擇...';
        }

        // 登入/註冊成功後，將關鍵資訊儲存
        localStorage.setItem('user_token', responseData.token);
        localStorage.setItem('user_id', responseData.user_id); 
        localStorage.setItem('display_name', responseData.display_name);
        
        // 關鍵步驟：導向伺服器選擇頁面
        window.location.href = 'server-select.html'; 

    } catch (error) {
        messageArea.textContent = `❌ 錯誤：${error.message}`;
    }
});