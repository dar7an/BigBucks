let apiKey

fetch('/config')
    .then(response => response.json())
    .then(config => {
        apiKey = config.API_KEY;
    });

function makePlotAPI(stockSymbol) {;
    fetch(`https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=${stockSymbol}&outputsize=full&apikey=${apiKey}`)
        .then(response => response.json())
        .then(data => {
            console.log("using API")
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

function makePlotnonAPI(stockSymbol, stock_data_json) {
    console.log("NOT using API");
    const stock_data = JSON.parse(stock_data_json);
    chartData = [];

    if (typeof stock_data === 'object' && stock_data !== null) {
        Object.keys(stock_data).forEach(stock_symbol => {
            const dates = Object.keys(stock_data[stock_symbol]);

            const x = dates.map(date => date); // Extracting dates
            const y = dates.map(date => parseFloat(stock_data[stock_symbol][date]["close_price"])); // Extracting close prices

            chartData.push({
                x: x,
                y: y,
                type: 'line',
                line: {color: 'blue'}
            });
        });
    } else {
        console.error('Invalid stock_data format. Expected an object.', stock_data);
    }

    const layout = {
        title: `Stock Prices for ${stockSymbol}`,
        xaxis: {
            title: 'Trading Day'
        },
        yaxis: {
            title: 'Close Price'
        }
    };

    console.log('Creating Plotly chart');
    Plotly.newPlot('myChart', chartData, layout);
}
