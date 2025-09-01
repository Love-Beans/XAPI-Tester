function get_x_token() {
    const token = localStorage.getItem('token');
    const headers = {};
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
        headers['Content-Type']='application/json';
    }
    return headers;
}
async function checkAuth(){
    //return true;
    try {
        // 验证 token 有效性
        const response = await fetch('/api/verify_token', {
            headers: get_x_token()
        });
        
        if (!response.ok) {
            // token 无效，跳转到登录页面
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = 'login.html';
            return false;
        }
        return true;
    } catch (error) {
        console.error('验证用户登录失败:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = 'login.html';
        return false;
    }
}
