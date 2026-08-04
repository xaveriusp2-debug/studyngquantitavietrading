const WebSocket = require('ws');
const https = require('https');
const fs = require('fs');

const wss = new WebSocket.Server({ port: 8080 });
console.log("==================================================");
console.log("🚀 Real-Time Market Data Server is running on port 8080");
console.log("==================================================");

let liveStockData = {};
const symbolsToFetch = ['BBCA.JK', 'GOTO.JK', 'BREN.JK', 'BRPT.JK', 'AMMN.JK', 'TLKM.JK', 'ASII.JK', 'BBMD.JK', 'PGEO.JK', 'CUAN.JK', 'BUMI.JK', 'ADRO.JK', 'SIDO.JK', 'KLBF.JK', 'UNVR.JK'];

// 1. Fetch Real-Time Data from Internet (Yahoo Finance API)
function fetchRealTimeData() {
    const symbols = symbolsToFetch.join(',');
    const url = `https://query1.finance.yahoo.com/v7/finance/quote?symbols=${symbols}`;

    https.get(url, {
        headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' }
    }, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
            try {
                const parsed = JSON.parse(data);
                if (parsed.quoteResponse && parsed.quoteResponse.result) {
                    const results = parsed.quoteResponse.result;
                    const updateData = { type: 'MARKET_DATA', data: {} };
                    
                    results.forEach(quote => {
                        const symbol = quote.symbol.replace('.JK', '');
                        updateData.data[symbol] = {
                            price: quote.regularMarketPrice,
                            change: quote.regularMarketChange,
                            changePercent: quote.regularMarketChangePercent,
                            volume: quote.regularMarketVolume || 0,
                        };
                    });
                    
                    liveStockData = updateData.data;

                    // Broadcast
                    wss.clients.forEach(client => {
                        if (client.readyState === WebSocket.OPEN) {
                            client.send(JSON.stringify(updateData));
                        }
                    });
                }
            } catch (err) {
                // console.error("Parse error:", err.message);
            }
        });
    }).on('error', (err) => {
        console.error("Fetch error:", err.message);
    });
}

// Fetch every 3 seconds to keep it fresh
setInterval(fetchRealTimeData, 3000);
fetchRealTimeData(); 

// 2. Optional Amibroker File Watcher
const dataFile = 'amidata.json';
if (!fs.existsSync(dataFile)) { fs.writeFileSync(dataFile, '{}'); }

fs.watch(dataFile, (eventType) => {
    if (eventType === 'change') {
        try {
            const data = fs.readFileSync(dataFile, 'utf8');
            if (data.trim() !== "") {
                const parsedData = JSON.parse(data);
                wss.clients.forEach(client => {
                    if (client.readyState === WebSocket.OPEN) {
                        client.send(JSON.stringify({ type: 'AMIBROKER_DATA', data: parsedData }));
                    }
                });
            }
        } catch (e) {}
    }
});

wss.on('connection', (ws) => {
    console.log('Client connected to real-time feed!');
    if (Object.keys(liveStockData).length > 0) {
        ws.send(JSON.stringify({ type: 'MARKET_DATA', data: liveStockData }));
    }
});
