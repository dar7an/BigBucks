function fetchConfigAndMakePlotAPI(stockSymbol) {
    fetch('/config')
        .then(response => response.json())
        .then(config => {
            apiKey = config.API_KEY;
            makePlotAPI(stockSymbol);
        });
}

function fetchConfigAndMakePlotCompSPY(stockSymbol, spysymbol) {
    fetch('/config')
        .then(response => response.json())
        .then(config => {
            apiKey = config.API_KEY;
            makeComparisonPlot(stockSymbol, spysymbol);
        });
}

function makePlotAPI(stockSymbol) {
    fetch(`https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=${stockSymbol}&outputsize=full&apikey=${apiKey}`)
        .then(response => response.json())
        .then(data => {
            if (!data['Time Series (Daily)']) {
                console.error('Time Series (Daily) data is not available');
                return;
            }
            console.log("Creating Plot")
            const dates = Object.keys(data['Time Series (Daily)']).reverse();
            const adjClosePrices = dates.map(date => parseFloat(data['Time Series (Daily)'][date]['4. close']));

            const chartData = [{
                x: dates,
                y: adjClosePrices,
                type: 'scatter',
                mode: 'lines',
                marker: {
                    color: 'blue'
                }
            }];

            const layout = {
                title: 'Stock Prices for ' + stockSymbol,
                xaxis: {
                    title: 'Date'
                },
                yaxis: {
                    title: 'Close Price'
                }
            };
            console.log('Creating Plotly chart');
            Plotly.newPlot('myChart', chartData, layout);
        })
        .catch(error => {
            console.error('Error fetching data from Alpha Vantage:', error);
        });
}

function makeComparisonPlot(stockSymbol, spysymbol) {
    let stockUrl = `https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=${stockSymbol}&outputsize=full&apikey=${apiKey}`;
    let spyUrl = `https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=${spysymbol}&outputsize=full&apikey=${apiKey}`;

    Promise.all([fetch(stockUrl).then(response => response.json()), fetch(spyUrl).then(response => response.json())])
        .then(([stockData, SPYData]) => {
            if (!stockData['Time Series (Daily)'] || !SPYData['Time Series (Daily)']) {
                console.error('Time Series (Daily) data is not available');
                return;
            }

            let dates = [];
            let stockReturns = [];
            let SPYReturns = [];

            for (let date in stockData['Time Series (Daily)']) {
                if (date in SPYData['Time Series (Daily)']) {
                    let stockReturn = stockData['Time Series (Daily)'][date]['4. close'] / stockData['Time Series (Daily)'][Object.keys(stockData['Time Series (Daily)'])[0]]['4. close'] - 1;
                    let SPYReturn = SPYData['Time Series (Daily)'][date]['4. close'] / SPYData['Time Series (Daily)'][Object.keys(SPYData['Time Series (Daily)'])[0]]['4. close'] - 1;
                    dates.push(date);
                    stockReturns.push(stockReturn);
                    SPYReturns.push(SPYReturn);
                }
            }

            let trace1 = {
                x: dates,
                y: stockReturns,
                mode: 'lines',
                name: stockSymbol
            };

            let trace2 = {
                x: dates,
                y: SPYReturns,
                mode: 'lines',
                name: 'SPY'
            };

            let data = [trace1, trace2];

            let layout = {
                title: 'Comparison of Returns with SPY',
                xaxis: {
                    title: 'Date'
                },
                yaxis: {
                    title: 'Return'
                }
            };

            Plotly.newPlot('comparisonChart', data, layout);
        })
        .catch(error => {
            console.error('Error fetching data from Alpha Vantage:', error);
        });
}