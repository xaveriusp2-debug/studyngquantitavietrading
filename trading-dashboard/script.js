// Mock Data representing Stockbit API response for trending stocks
// based on Technicals and Right Issue

const mockStockData = [
    {
        code: 'BBCA',
        name: 'Bank Central Asia Tbk.',
        price: 'Rp 9,800',
        trend: 'Strong Uptrend',
        trendStatus: 'bullish',
        technical: 'RSI: 65 | MACD Golden Cross',
        rightIssue: 'Tidak Ada',
        riStatus: 'none',
        action: 'Hold'
    },
    {
        code: 'GOTO',
        name: 'GoTo Gojek Tokopedia Tbk.',
        price: 'Rp 65',
        trend: 'Rebound',
        trendStatus: 'bullish',
        technical: 'Breakout MA20 | Volume Spikes',
        rightIssue: 'Mendatang (Q3)',
        riStatus: 'ri-active',
        action: 'Buy'
    },
    {
        code: 'BREN',
        name: 'Barito Renewables Energy Tbk.',
        price: 'Rp 5,450',
        trend: 'Correction',
        trendStatus: 'bearish',
        technical: 'RSI: 80 (Overbought)',
        rightIssue: 'Selesai',
        riStatus: 'none',
        action: 'Take Profit'
    },
    {
        code: 'BRPT',
        name: 'Barito Pacific Tbk.',
        price: 'Rp 1,020',
        trend: 'Sideways',
        trendStatus: 'neutral',
        technical: 'Consolidation at Support',
        rightIssue: 'Pengumuman RUPSLB',
        riStatus: 'ri-active',
        action: 'Watch'
    },
    {
        code: 'AMMN',
        name: 'Amman Mineral Internasional',
        price: 'Rp 8,200',
        trend: 'Uptrend',
        trendStatus: 'bullish',
        technical: 'MA50 Support Hold',
        rightIssue: 'Tidak Ada',
        riStatus: 'none',
        action: 'Buy'
    }
];

let realTimePrices = {}; // Store real prices from API

const mockFundamentalData = [
    {
        code: 'SIDO',
        name: 'Sido Muncul Tbk.',
        laporan: 'Laba bersih naik 15% YoY, Margin Sehat',
        posisi: 'Market Leader (Herbal)',
        manajemen: 'Track Record Kuat, GCG Baik',
        valuasi: 'PER 18x (Undervalued)',
        valuasiStatus: 'bullish',
        action: 'Buy'
    },
    {
        code: 'ASII',
        name: 'Astra International Tbk.',
        laporan: 'Pendapatan stabil, Kas melimpah',
        posisi: 'Konglomerasi Terbesar',
        manajemen: 'Profesional, Sangat Berpengalaman',
        valuasi: 'PBV 1.2x (Sangat Murah)',
        valuasiStatus: 'bullish',
        action: 'Accumulate'
    },
    {
        code: 'KLBF',
        name: 'Kalbe Farma Tbk.',
        laporan: 'Pertumbuhan EPS konsisten 8-10%',
        posisi: 'Market Leader (Farmasi)',
        manajemen: 'Inovatif, Ekspansi Regional',
        valuasi: 'PER 25x (Wajar)',
        valuasiStatus: 'neutral',
        action: 'Hold'
    },
    {
        code: 'UNVR',
        name: 'Unilever Indonesia Tbk.',
        laporan: 'Penurunan margin, Laba tertekan',
        posisi: 'Market Leader (FMCG)',
        manajemen: 'Transisi Strategi',
        valuasi: 'PER 30x (Premium)',
        valuasiStatus: 'bearish',
        action: 'Wait & See'
    }
];

// Function to render table rows
function renderTable(data) {
    const tbody = document.getElementById('stock-data-body');
    tbody.innerHTML = '';

    data.forEach(stock => {
        const tr = document.createElement('tr');
        
        let trendBadgeClass = '';
        if(stock.trendStatus === 'bullish') trendBadgeClass = 'bullish';
        else if(stock.trendStatus === 'bearish') trendBadgeClass = 'bearish';
        else trendBadgeClass = 'neutral';

        let riBadge = stock.riStatus === 'ri-active' 
            ? `<span class="badge ri-active">${stock.rightIssue}</span>`
            : stock.rightIssue;

        tr.innerHTML = `
            <td class="stock-code">${stock.code}</td>
            <td>${stock.name}</td>
            <td>${stock.price}</td>
            <td><span class="badge ${trendBadgeClass}">${stock.trend}</span></td>
            <td style="font-size: 0.9em; color: var(--text-muted);">${stock.technical}</td>
            <td>${riBadge}</td>
            <td><button class="btn-action" onclick="alert('Membuka detail ${stock.code} di platform broker...')">${stock.action}</button></td>
        `;
        tbody.appendChild(tr);
    });
}

function renderFundamentalTable(data) {
    const tbody = document.getElementById('fundamental-data-body');
    if (!tbody) return;
    
    tbody.innerHTML = '';

    data.forEach(stock => {
        const tr = document.createElement('tr');
        
        let valBadgeClass = '';
        if(stock.valuasiStatus === 'bullish') valBadgeClass = 'bullish';
        else if(stock.valuasiStatus === 'bearish') valBadgeClass = 'bearish';
        else valBadgeClass = 'neutral';

        tr.innerHTML = `
            <td class="stock-code">${stock.code}</td>
            <td>${stock.name}</td>
            <td style="font-size: 0.9em; color: var(--text-muted);">${stock.laporan}</td>
            <td><span class="badge" style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2); color: var(--primary);">${stock.posisi}</span></td>
            <td style="font-size: 0.9em; color: var(--text-muted);">${stock.manajemen}</td>
            <td><span class="badge ${valBadgeClass}">${stock.valuasi}</span></td>
            <td><button class="btn-action" style="background: var(--purple);" onclick="alert('Membuka riset fundamental ${stock.code}...')">${stock.action}</button></td>
        `;
        tbody.appendChild(tr);
    });
}

// Simulate real-time updates for IHSG
function simulateRealTimeData() {
    const ihsgElement = document.getElementById('ihsg-value');
    let baseValue = 7245.12;

    setInterval(() => {
        // Random fluctuation between -5 and +5
        const fluctuation = (Math.random() * 10 - 5);
        baseValue += fluctuation;
        
        // Update UI
        ihsgElement.innerText = baseValue.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        
        // Change color based on fluctuation
        const changeElement = ihsgElement.nextElementSibling;
        if(fluctuation >= 0) {
            changeElement.innerText = '+' + (fluctuation/baseValue * 100).toFixed(2) + '%';
            changeElement.className = 'change positive';
        } else {
            changeElement.innerText = (fluctuation/baseValue * 100).toFixed(2) + '%';
            changeElement.className = 'change negative';
        }
    }, 3000); // Update every 3 seconds
}

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', () => {
    // Render initial data
    renderTable(mockStockData);
    renderFundamentalTable(mockFundamentalData);
    
    // Start simulation
    simulateRealTimeData();

    // Filter interaction
    document.getElementById('filter-trend').addEventListener('change', (e) => {
        const val = e.target.value;
        // Simple mock filter logic
        if(val === 'all') {
            renderTable(mockStockData);
        } else if (val === 'tech') {
            renderTable(mockStockData.filter(s => s.code === 'GOTO'));
        } else if (val === 'energy') {
            renderTable(mockStockData.filter(s => s.code === 'BREN' || s.code === 'BRPT' || s.code === 'AMMN'));
        } else if (val === 'finance') {
            renderTable(mockStockData.filter(s => s.code === 'BBCA'));
        }
    });

    startRunningTrade();
    simulatePriceFluctuations();
    startHFTSystem();
    connectAmibrokerBridge();
});

// Amibroker WebSocket Connection
function connectAmibrokerBridge() {
    const statusEl = document.getElementById('amibroker-status');
    const ws = new WebSocket('ws://localhost:8080');
    
    ws.onopen = () => {
        statusEl.innerHTML = '<span style="width: 6px; height: 6px; background: var(--success); border-radius: 50%; display: inline-block;"></span> Amibroker: Connected';
        statusEl.style.color = 'var(--success)';
        console.log("Connected to local Amibroker bridge.");
    };

    ws.onmessage = (event) => {
        try {
            const payload = JSON.parse(event.data);
            if (payload.type === 'MARKET_DATA') {
                realTimePrices = payload.data;
                updateUIPrices();
            } else if (payload.type === 'AMIBROKER_DATA') {
                injectAmibrokerSignal(payload.data);
            }
        } catch (e) {
            console.error("Invalid data from bridge", e);
        }
    };

    ws.onerror = () => {
        statusEl.innerHTML = '<span style="width: 6px; height: 6px; background: var(--danger); border-radius: 50%; display: inline-block;"></span> Amibroker: Disconnected';
        statusEl.style.color = 'var(--danger)';
    };

    ws.onclose = () => {
        statusEl.innerHTML = '<span style="width: 6px; height: 6px; background: var(--danger); border-radius: 50%; display: inline-block;"></span> Amibroker: Disconnected (Retrying...)';
        statusEl.style.color = 'var(--danger)';
        setTimeout(connectAmibrokerBridge, 3000); // Auto reconnect
    };
}

// Function to handle real incoming Amibroker Data
function injectAmibrokerSignal(data) {
    const signalList = document.getElementById('ai-signals-list');
    if (!signalList) return;

    // Detect if this is a bullish or bearish setup based on simple EMA cross logic
    // Amibroker exports current price and ema9
    const isBuy = data.close > data.ema9;
    const action = isBuy ? 'AFL BUY SIGNAL' : 'AFL SELL SIGNAL';
    const color = isBuy ? 'var(--success)' : 'var(--danger)';
    const bg = isBuy ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)';
    const border = isBuy ? 'rgba(16, 185, 129, 0.5)' : 'rgba(239, 68, 68, 0.5)';
    const reason = isBuy ? 'Amibroker: Cross Up EMA9' : 'Amibroker: Cross Down EMA9';

    const now = new Date();
    const hh = String(now.getHours()).padStart(2, '0');
    const mm = String(now.getMinutes()).padStart(2, '0');
    const ss = String(now.getSeconds()).padStart(2, '0');
    const timestampStr = `${hh}:${mm}:${ss}.000`;

    const signalItem = document.createElement('div');
    signalItem.style.cssText = `padding: 0.8rem; border-radius: 6px; background: ${bg}; border-left: 4px solid ${color}; display: flex; justify-content: space-between; align-items: center; animation: fadeInUp 0.3s ease; flex-shrink: 0; box-shadow: 0 0 10px ${border};`;
    
    signalItem.innerHTML = `
        <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
            <span style="color: var(--text-muted); font-size: 0.85rem; font-family: monospace;">[${timestampStr}]</span>
            <strong style="color: #fff; font-size: 1.1rem; width: 50px; text-align: center;">${data.ticker}</strong>
            <span style="color: #fff; font-weight: bold; padding: 0.2rem 0.6rem; border-radius: 4px; background: ${color}; font-size: 0.8rem;">${action}</span>
            <span style="color: var(--text-main); font-size: 0.9rem;">${reason}</span>
        </div>
        <div style="text-align: right; min-width: 100px;">
            <div style="font-size: 0.9rem; color: var(--text-muted);">Real Price: <span style="color: #fff; font-family: monospace;">Rp${data.close.toLocaleString()}</span></div>
            <div style="font-size: 0.85rem; color: var(--text-muted); font-family: monospace;">Vol: ${(data.volume/100).toLocaleString()} Lot</div>
        </div>
    `;
    
    signalList.prepend(signalItem);

    if (signalList.children.length > 50) {
        signalList.removeChild(signalList.lastChild);
    }
}

// High-Frequency Trading (HFT) AI Signals
function startHFTSystem() {
    const signalList = document.getElementById('ai-signals-list');
    const datetimeElement = document.getElementById('live-datetime');
    if (!signalList || !datetimeElement) return;

    // Set base time to 21 April 2026 09:00:00 as requested
    let baseDate = new Date("2026-04-21T09:00:00");
    
    // Simulate high frequency timer
    setInterval(() => {
        baseDate.setMilliseconds(baseDate.getMilliseconds() + 115); // fast forward 115ms per tick
        
        const hh = String(baseDate.getHours()).padStart(2, '0');
        const mm = String(baseDate.getMinutes()).padStart(2, '0');
        const ss = String(baseDate.getSeconds()).padStart(2, '0');
        const ms = String(baseDate.getMilliseconds()).padStart(3, '0');
        datetimeElement.innerText = `21 April 2026 ${hh}:${mm}:${ss}.${ms}`;
    }, 115);

    const stocks = ['GOTO', 'BBCA', 'BREN', 'BRPT', 'AMMN', 'TLKM', 'ASII', 'CUAN', 'BUMI', 'PGEO', 'PANI', 'ADRO'];
    const buyPatterns = ['Breakout Resistance Vol Tinggi', 'Lonjakan Akumulasi HAKA', 'Bandar Tarik Antrean Offer', 'Golden Cross EMA 1m', 'Pantulan Support Kuat VWAP'];
    const sellPatterns = ['Jebol Support Vol Tinggi', 'HAKI Masif di Bid', 'Distribusi Bandar Terdeteksi', 'Gagal Breakout (False Break)', 'Divergence Negatif MACD'];

    function addSignal() {
        if (Math.random() > 0.3) { // 70% chance to emit a signal per interval
            const stock = stocks[Math.floor(Math.random() * stocks.length)];
            const isBuy = Math.random() > 0.4; // Slightly more buy signals
            const action = isBuy ? 'STRONG BUY' : 'SELL/CUT';
            const color = isBuy ? 'var(--success)' : 'var(--danger)';
            const bg = isBuy ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)';
            const border = isBuy ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)';
            
            const reason = isBuy ? buyPatterns[Math.floor(Math.random() * buyPatterns.length)] : sellPatterns[Math.floor(Math.random() * sellPatterns.length)];
            
            // USE REAL PRICE IF AVAILABLE
            let price = 50;
            if (realTimePrices[stock] && realTimePrices[stock].price) {
                price = realTimePrices[stock].price;
            } else {
                price = Math.floor(Math.random() * 9000) + 50;
            }
            
            const target = isBuy ? price + Math.floor(price * (Math.random() * 0.03 + 0.01)) : price - Math.floor(price * (Math.random() * 0.03 + 0.01));

            const hh = String(baseDate.getHours()).padStart(2, '0');
            const mm = String(baseDate.getMinutes()).padStart(2, '0');
            const ss = String(baseDate.getSeconds()).padStart(2, '0');
            const ms = String(baseDate.getMilliseconds()).padStart(3, '0');
            const timestampStr = `${hh}:${mm}:${ss}.${ms}`;

            const signalItem = document.createElement('div');
            signalItem.style.cssText = `padding: 0.8rem; border-radius: 6px; background: ${bg}; border-left: 4px solid ${color}; display: flex; justify-content: space-between; align-items: center; animation: fadeInUp 0.3s ease; flex-shrink: 0;`;
            
            signalItem.innerHTML = `
                <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                    <span style="color: var(--text-muted); font-size: 0.85rem; font-family: monospace;">[${timestampStr}]</span>
                    <strong style="color: var(--primary); font-size: 1.1rem; width: 50px; text-align: center;">${stock}</strong>
                    <span style="color: ${color}; font-weight: bold; padding: 0.2rem 0.6rem; border-radius: 4px; background: ${border}; font-size: 0.8rem;">${action}</span>
                    <span style="color: var(--text-main); font-size: 0.9rem;">${reason}</span>
                </div>
                <div style="text-align: right; min-width: 100px;">
                    <div style="font-size: 0.9rem; color: var(--text-muted);">Entry: <span style="color: #fff; font-family: monospace;">Rp${price.toLocaleString()}</span></div>
                    <div style="font-size: 0.85rem; color: var(--warning); font-family: monospace;">Target: Rp${target.toLocaleString()}</div>
                </div>
            `;
            
            signalList.prepend(signalItem);

            // Keep list bounded to prevent memory leak
            if (signalList.children.length > 50) {
                signalList.removeChild(signalList.lastChild);
            }
        }
    }

    // Broker Summary logic
    const brokers = ['YP', 'CC', 'PD', 'NI', 'BK', 'AK', 'KZ', 'CS', 'ZP', 'RX', 'LG', 'DX'];
    function updateBrokerSummary() {
        const brokerList = document.getElementById('broker-list');
        if (!brokerList) return;
        
        let content = '';
        for(let i=0; i<8; i++) {
            const buyer = brokers[Math.floor(Math.random() * brokers.length)];
            let seller = brokers[Math.floor(Math.random() * brokers.length)];
            while(seller === buyer) seller = brokers[Math.floor(Math.random() * brokers.length)];
            
            const netVol = Math.floor(Math.random() * 80000) + 5000;
            
            // Highlight foreign brokers
            const isForeignBuyer = ['BK', 'AK', 'KZ', 'CS', 'ZP', 'RX'].includes(buyer);
            const isForeignSeller = ['BK', 'AK', 'KZ', 'CS', 'ZP', 'RX'].includes(seller);
            
            const buyerStyle = isForeignBuyer ? 'color: var(--primary); font-weight: bold;' : 'color: var(--success); font-weight: bold;';
            const sellerStyle = isForeignSeller ? 'color: var(--primary); font-weight: bold; text-align: right;' : 'color: var(--danger); font-weight: bold; text-align: right;';

            content += `
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.4rem 0.5rem; background: rgba(255,255,255,0.02); border-radius: 4px; animation: fadeInDown 0.3s ease;">
                    <span style="${buyerStyle} width: 30px;">${buyer}</span>
                    <span style="color: var(--text-main); font-size: 0.85rem;">${netVol.toLocaleString()}L</span>
                    <span style="${sellerStyle} width: 30px;">${seller}</span>
                </div>
            `;
        }
        brokerList.innerHTML = content;
    }

    // Attempt to add a signal rapidly
    setInterval(() => {
        addSignal();
    }, 450); // Every 450ms

    // Update broker summary periodically
    updateBrokerSummary();
    setInterval(updateBrokerSummary, 1200);
}

// Real-Time Trade Ticker Simulation (Running Trade)
function startRunningTrade() {
    const tickerContent = document.getElementById('ticker-content');
    if (!tickerContent) return;

    const stocks = ['GOTO', 'BBCA', 'BREN', 'BRPT', 'AMMN', 'TLKM', 'ASII', 'BBMD', 'PGEO', 'CUAN', 'BUMI'];
    const actions = ['HAKA', 'HAKI'];
    
    function createTickerItem() {
        const stock = stocks[Math.floor(Math.random() * stocks.length)];
        // 60% chance to HAKA for positive bias
        const action = Math.random() > 0.4 ? 'HAKA' : 'HAKI';
        const volume = Math.floor(Math.random() * 50000) + 100;
        
        let price = 50;
        if (realTimePrices[stock] && realTimePrices[stock].price) {
            price = realTimePrices[stock].price;
        } else {
            price = Math.floor(Math.random() * 9000) + 50;
        }
        
        const isBuy = action === 'HAKA';
        const colorClass = isBuy ? 'ticker-buy' : 'ticker-sell';
        const icon = isBuy ? '▲' : '▼';
        
        return `<span class="ticker-item ${colorClass}">${icon} ${stock} Rp${price} | Vol: ${volume.toLocaleString()} Lot [${action}]</span>`;
    }

    // Populate initial items
    let content = '';
    for(let i=0; i<20; i++) {
        content += createTickerItem();
    }
    tickerContent.innerHTML = content;

    // Periodically update some elements to make it feel alive
    setInterval(() => {
        const currentContent = tickerContent.innerHTML;
        // Remove first item and append new one if possible, but innerHTML manipulation might interrupt animation.
        // Easiest is to just rebuild a new long string of items every 25s (duration of animation)
    }, 25000);
}

// Simulate Price Fluctuations in the Technical Table
function simulatePriceFluctuations() {
    // This is now replaced by updateUIPrices called directly from websocket
}

function updateUIPrices() {
    const rows = document.querySelectorAll('#stock-data-body tr');
    if (rows.length === 0) return;
    
    rows.forEach(row => {
        const codeCell = row.cells[0];
        const priceCell = row.cells[2];
        const stockCode = codeCell.innerText;
        
        if (realTimePrices[stockCode]) {
            const realData = realTimePrices[stockCode];
            const currentPriceStr = priceCell.innerText.replace(/[^0-9]/g, '');
            const displayedPrice = parseInt(currentPriceStr) || 0;
            const newPrice = Math.floor(realData.price);
            
            if (displayedPrice !== newPrice) {
                priceCell.innerText = 'Rp ' + newPrice.toLocaleString('en-US');
                
                // Flash animation
                const isUp = newPrice > displayedPrice;
                const originalBg = row.style.backgroundColor;
                
                row.style.transition = 'background-color 0.3s ease';
                row.style.backgroundColor = isUp ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)';
                priceCell.style.color = isUp ? 'var(--success)' : 'var(--danger)';
                priceCell.style.fontWeight = 'bold';
                
                setTimeout(() => {
                    row.style.backgroundColor = originalBg || ''; // Reset
                    priceCell.style.color = '';
                    priceCell.style.fontWeight = 'normal';
                }, 1200);
            }
        }
    });
    
    // Also update IHSG if GOTO/BBCA data exists as a proxy
    const ihsgElement = document.getElementById('ihsg-value');
    if (ihsgElement && realTimePrices['BBCA']) {
        // Just a slight random jitter based on real data to make IHSG look alive
        let baseValue = parseFloat(ihsgElement.innerText.replace(/,/g, ''));
        const fluctuation = (Math.random() * 4 - 2);
        baseValue += fluctuation;
        
        ihsgElement.innerText = baseValue.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        
        const changeElement = ihsgElement.nextElementSibling;
        if(fluctuation >= 0) {
            changeElement.innerText = '+' + (fluctuation/baseValue * 100).toFixed(2) + '%';
            changeElement.className = 'change positive';
        } else {
            changeElement.innerText = (fluctuation/baseValue * 100).toFixed(2) + '%';
            changeElement.className = 'change negative';
        }
    }
}

