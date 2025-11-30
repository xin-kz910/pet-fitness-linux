// frontend/js/lobby_app.js (最終優化版)
import { getPetStatus } from './api_client.js';

// DOM 元素定義
const petNameEl = document.getElementById('pet-name');
const petLevelEl = document.getElementById('pet-level');
const serverIdEl = document.getElementById('server-id');
const lobbyTitleEl = document.getElementById('lobby-title');
const myPetImgEl = document.getElementById('my-pet-img');
const myPetNameTagEl = document.querySelector('#my-pet .pet-name-tag');

const chatBox = document.getElementById('chat-box');
const chatHeader = document.getElementById('chat-header');
const closeChatBtn = document.getElementById('close-chat-btn');
const lobbyContainer = document.getElementById('lobby-container');
const logoutBtn = document.getElementById('logout-btn');


// ======================================================
// 聊天框互動邏輯 (放在初始化函數外部，因為它被其他函數呼叫)
// ======================================================
function closeChatBox() {
    chatBox.style.display = 'none';
}

/**
 * 處理點擊寵物，彈出聊天框
 */
function handlePetClick(e) {
    const petAvatar = e.target.closest('.pet-avatar');
    if (petAvatar && petAvatar.id !== 'my-pet') {
        const targetName = petAvatar.querySelector('.pet-name-tag').textContent;
        const targetId = petAvatar.getAttribute('data-user-id');
        
        // 更新聊天框標題
        chatHeader.innerHTML = `💬 與 ${targetName} 通訊中 <button id="close-chat-btn" style="float: right;">X</button>`;
        
        // 顯示聊天框
        chatBox.style.display = 'flex';
        
        // 重新綁定關閉按鈕事件（因為 innerHTML 被替換了）
        // 這裡我們需要重新取得新的按鈕元素，然後綁定事件
        document.querySelector('#chat-box #close-chat-btn').onclick = closeChatBox;
        
        console.log(`準備與用戶 ID ${targetId} 進行即時通訊`);
    }
}

// ======================================================
// 初始化函數
// ======================================================

async function initializeLobby() {
    const token = localStorage.getItem('user_token');
    const selected_server_id = localStorage.getItem('selected_server_id');
    
    // 1. 檢查 Token 和 Server ID
    if (!token || !selected_server_id) {
        alert('登入資訊或伺服器未選擇，請重新登入！');
        window.location.href = 'login.html';
        return;
    }

    // 2. 更新 UI 資訊
    serverIdEl.textContent = `伺服器：${selected_server_id}`;
    lobbyTitleEl.textContent = `🌍 虛擬大廳 (Server ${selected_server_id})`;

    try {
        // 3. 呼叫組員 A 的 API 獲取寵物狀態
        const petData = await getPetStatus();

        // 4. 更新寵物資訊到 UI (真實資料)
        petNameEl.textContent = `寵物名稱：${petData.name}`;
        petLevelEl.textContent = `等級：${petData.level}`;
        myPetNameTagEl.textContent = petData.display_name;
        // 根據寵物狀態更新圖片: myPetImgEl.src = `assets/pet-${petData.status}.png`;

    } catch (error) {
        // 4. 更新寵物資訊到 UI (模擬資料)
        console.error('無法載入寵物狀態，後端服務可能未啟動:', error);
        petNameEl.textContent = `寵物名稱：Test Pet`;
        petLevelEl.textContent = `精神狀態：99`;
        myPetNameTagEl.textContent = localStorage.getItem('display_name') || '玩家';
    }
    
    // 5. 綁定所有事件監聽器 (確保所有元素已載入)
    
    // 登出功能
    logoutBtn.addEventListener('click', () => {
        localStorage.clear(); // 清除所有儲存資訊
        alert('已登出。');
        window.location.href = 'login.html';
    });
    
    // 監聽大廳容器的點擊事件（用於點擊寵物）
    lobbyContainer.addEventListener('click', handlePetClick);

    // 初始化關閉按鈕事件 (針對初始 HTML 內建的按鈕)
    closeChatBtn.onclick = closeChatBox;
}

// ======================================================
// 腳本入口點：在所有程式碼定義之後執行初始化
// ======================================================
initializeLobby();

// TODO: 後續步驟 - 實作寵物隨機移動和大廳 WebSockets (組員 D 的部分)