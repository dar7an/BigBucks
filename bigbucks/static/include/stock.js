let apiKey

function fetchConfigAndMakePlotAPI(stockSymbol) {
    fetch('/config')
        .then(response => response.json())
        .then(config => {
            apiKey = config.API_KEY;
            makePlotAPI(stockSymbol);
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

