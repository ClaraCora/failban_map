// static/js/dashboard.js

// --- 全局变量，用于在函数间共享最新数据 ---
let latestMapData = null;
let latestServerConfig = null;

/**
 * 唯一的绘图函数。
 */
function renderMap(container, mapData, serverConfig) {
    if (!mapData || mapData.length === 0) {
        container.innerHTML = '<div style="text-align:center; padding-top: 40%;">地图数据为空。</div>';
        return;
    }
    container.innerHTML = ''; 

    const traces = [];
    const top10Countries = mapData.slice(0, 10);
    const lineLons = [];
    const lineLats = [];
    mapData.forEach(row => {
        lineLons.push(row.longitude, serverConfig.lon, null);
        lineLats.push(row.latitude, serverConfig.lat, null);
    });
    traces.push({
        type: 'scattergeo', mode: 'lines', lon: lineLons, lat: lineLats,
        line: { width: 1, color: '#00c6ff' }, hoverinfo: 'none'
    });
    traces.push({
        type: 'scattergeo', mode: 'markers+text', lon: [serverConfig.lon], lat: [serverConfig.lat],
        text: [serverConfig.name], textposition: 'top right',
        textfont: { color: '#00ff00', size: 12, family: 'Roboto' },
        marker: { color: '#00ff00', size: 15, symbol: 'star' }, hoverinfo: 'none'
    });
    traces.push({
        type: 'scattergeo', mode: 'text', lon: top10Countries.map(d => d.longitude), lat: top10Countries.map(d => d.latitude),
        text: top10Countries.map(d => `<b>${d.emoji} ${d['国家/地区']}</b><br>${d['总封禁次数']}次 / ${d['独立IP数']}IPs`),
        textfont: { color: '#ffffff', size: 10, family: 'Roboto' }, hoverinfo: 'none'
    });
    const layout = {
        title: { text: '全球恶意扫描防御态势', font: { color: 'white', size: 20 } },
        showlegend: false,
        geo: {
            projection: { type: 'orthographic', rotation: { lon: -100, lat: 40 } },
            showland: true, landcolor: '#2a3f5f',
            showcountries: true, countrycolor: '#50678b',
            showocean: true, oceancolor: 'rgba(13, 26, 46, 1)',
            bgcolor: 'rgba(0,0,0,0)',
        },
        dragmode: 'orbit',
        margin: { r: 0, t: 40, l: 0, b: 0 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)'
    };
    const config = { responsive: false, displayModeBar: true };
    Plotly.newPlot(container, traces, layout, config);
}

function renderList(elementId, data, keyField, valueField) {
    const list = document.getElementById(elementId);
    list.innerHTML = '';
    if (!data || data.length === 0) {
        list.innerHTML = '<li><span>无数据</span><span>-</span></li>';
        return;
    }
    data.forEach(item => {
        const li = document.createElement('li');
        li.innerHTML = `<span>${item[keyField]}</span><span>${item[valueField]}</span>`;
        list.appendChild(li);
    });
}

async function updateDashboard() {
    const statusDiv = document.getElementById('status');
    try {
        statusDiv.innerText = '正在获取最新数据...';
        const response = await fetch('/data');
        if (!response.ok) throw new Error(`服务器错误: ${response.statusText}`);
        const data = await response.json();
        if (data.error) throw new Error(data.error);

        // 1. 将获取到的最新数据存入全局变量
        latestMapData = data.map_data;
        latestServerConfig = data.server_config;

        // 2. 只更新列表数据，不再处理任何视图逻辑
        renderList('country-list', data.country_table, 'display_name', '总封禁次数');
        renderList('asn-list', data.asn_table, '机构/ISP (ASN)', '封禁次数');
        
        statusDiv.innerText = `数据更新于: ${new Date().toLocaleTimeString()}`;
    } catch (error) {
        statusDiv.innerText = `加载失败: ${error.message}`;
        console.error(error);
    }
}

// --- Main Execution ---
document.addEventListener('DOMContentLoaded', () => {
    const refreshBtn = document.getElementById('refresh-btn');
    const switchBtn = document.getElementById('switch-view-btn');
    const mapContainer = document.getElementById('map-container');
    const kasperskyContainer = document.getElementById('kaspersky-container');

    window.addEventListener('resize', () => {
        if (!mapContainer.classList.contains('hidden')) {
            Plotly.Plots.resize(mapContainer);
        }
    });

    refreshBtn.addEventListener('click', async () => {
        refreshBtn.disabled = true;
        document.getElementById('status').innerText = '正在从日志文件生成新报告...';
        try {
            const response = await fetch('/refresh', { method: 'POST' });
            const result = await response.json();
            document.getElementById('status').innerText = result.message;
            if (result.status === 'success') {
                await updateDashboard();
            }
        } catch (error) {
            document.getElementById('status').innerText = `刷新时发生错误: ${error.message}`;
        } finally {
            refreshBtn.disabled = false;
        }
    });

    switchBtn.addEventListener('click', () => {
        const isNativeViewHidden = mapContainer.classList.toggle('hidden');
        kasperskyContainer.classList.toggle('hidden');

        // 如果本地图即将变为可见 (isNativeViewHidden 为 false)
        if (!isNativeViewHidden) {
            // 检查是否已绘制，避免重复绘制
            if (mapContainer.querySelector('.plotly') === null && latestMapData) {
                renderMap(mapContainer, latestMapData, latestServerConfig);
            }
        }
    });

    // Initial data load
    updateDashboard();
});