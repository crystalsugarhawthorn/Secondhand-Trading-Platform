// 商品视图切换、订单倒计时、菜单切换等前端交互

// 视图切换功能
function toggleView(view) {
    const container = document.getElementById('product-container');
    if (view === 'list') {
        container.classList.remove('product-grid');
        container.classList.add('product-list');
    } else {
        container.classList.remove('product-list');
        container.classList.add('product-grid');
    }
}

// 订单支付倒计时
function updateCountdowns() {
    const countdowns = document.querySelectorAll('.countdown');
    const now = new Date();
    
    countdowns.forEach(countdown => {
        const created = new Date(countdown.dataset.created);
        const elapsed = (now - created) / 1000; // 秒数
        const remaining = Math.max(0, 60 - Math.floor(elapsed)); // 剩余秒数(5分钟)
        
        if (remaining <= 0) {
            countdown.querySelector('.time-remaining').textContent = '已超时';
            
            // 获取订单ID
            const orderRow = countdown.closest('tr');
            if (orderRow) {
                const orderId = orderRow.querySelector('td:first-child a').textContent;
                if (orderId) {
                    // 找到去付款按钮并修改为取消订单
                    const payBtn = orderRow.querySelector('a[href^="/pay/"]');
                    if (payBtn) {
                        payBtn.textContent = '取消订单';
                        payBtn.href = `/order/cancel/${orderId}`;
                        payBtn.classList.remove('btn-warning');
                        payBtn.classList.add('btn-danger');
                        
                        // 自动点击取消订单按钮
                        setTimeout(() => {
                            payBtn.click();
                        }, 1000);
                    }
                }
            }
        } else {
            const minutes = Math.floor(remaining / 60);
            const seconds = remaining % 60;
            countdown.querySelector('.time-remaining').textContent = 
                `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
    });
}

// 菜单切换功能
function toggleMenu() {
    const menu = document.querySelector('.nav-menu');
    menu.classList.toggle('active');
}

// 初始化倒计时
document.addEventListener('DOMContentLoaded', () => {
    // 启动倒计时
    updateCountdowns();
    // 每秒更新一次
    setInterval(updateCountdowns, 1000);
});