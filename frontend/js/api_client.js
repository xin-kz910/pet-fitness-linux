// frontend/js/api_client.js

// 統一的基礎 URL，用於處理 Nginx 反向代理
const BASE_URL = window.location.origin;

/**
 * 統一處理所有 REST API 請求
 * @param {string} endpoint - 應用程式內部的 API 路徑 (例如: /api/login)
 * @param {string} method - HTTP 方法 (例如: 'POST', 'GET')
 * @param {object} data - 請求體 (Request Body)
 * @returns {Promise<object>} - 成功時回傳 data 區塊
 */
async function callApi(endpoint, method = 'GET', data = null) {
    const server_id = localStorage.getItem('selected_server_id');
    const token = localStorage.getItem('user_token');
    
    if (!server_id && endpoint !== '/api/register' && endpoint !== '/api/login') {
        // 登入/註冊外，沒有選擇伺服器則報錯
        throw new Error("SERVER_NOT_SELECTED: 請先選擇伺服器。");
    }

    // 實體路徑範例: /serverA/api/login
    // 注意: 我們在登入/註冊成功後，才會確定最終的 server_id
    const prefix = server_id ? `/server${server_id}` : '';
    const url = `${BASE_URL}${prefix}${endpoint}`;
    
    const headers = {
        'Content-Type': 'application/json',
    };

    if (token) {
        // 授權 Header，組員 A 應該使用 Bearer Token
        headers['Authorization'] = `Bearer ${token}`; 
    }

    const config = {
        method: method,
        headers: headers,
    };

    if (data) {
        config.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, config);
        const json = await response.json();
        
        if (json.success === false) {
            // 處理後端回傳的錯誤 (例如: INVALID_CREDENTIALS)
            console.error('API Error:', json.error.code, json.error.message);
            throw new Error(json.error.message);
        }
        return json.data;
    } catch (error) {
        console.error('網路或解析錯誤:', error);
        throw new Error(`網路錯誤: ${error.message}`);
    }
}

// ===============================================
// 實作 組員 A 負責的 API 服務
// ===============================================

export async function login(username, password) {
    // 呼叫 API 時也不傳 server_id
    return callApi('/api/login', 'POST', { 
        username, 
        password
    });
}

export async function register(username, password, display_name) {
    // 呼叫 API 時也不傳 server_id
    return callApi('/api/register', 'POST', {
        username,
        password,
        display_name
    });
}

export async function getPetStatus() {
    return callApi('/api/pet/status', 'GET');
}