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

function fetchConfigAndMakeDailyChangePlot(stocksymbol, spysymbol) {
    fetch('/config')
        .then(response => response.json())
        .then(config => {
            apiKey = config.API_KEY;
            makeDailyChangePlot(stocksymbol, spysymbol);
        });
}

function fetchConfigAndMakeScatterPlot(stocksymbol, spysymbol) {
    fetch('/config')
        .then(response => response.json())
        .then(config => {
            apiKey = config.API_KEY;
            makeScatterPlot(stocksymbol, spysymbol);
        });
}

function regressionLine(x, y) {
    let n = y.length;
    let sum_x = 0;
    let sum_y = 0;
    let sum_xy = 0;
    let sum_xx = 0;
    for (let i = 0; i < y.length; i++) {
        sum_x += x[i];
        sum_y += y[i];
        sum_xy += (x[i]*y[i]);
        sum_xx += (x[i]*x[i]);
    }
    let slope = (n * sum_xy - sum_x * sum_y) / (n*sum_xx - sum_x * sum_x);
    let intercept = (sum_y - slope * sum_x) / n;
    return x.map(val => slope * val + intercept);
}

function makePlotAPI(stockSymbol) {
    fetch(`https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=${stockSymbol}&outputsize=full&apikey=${apiKey}`)
        .then(response => response.json())
        .then(data => {
            if (!data['Time Series (Daily)']) {
                console.error('Time Series (Daily) data is not available');
                return;
            }
            console.log("Creating Plot")
            const dates = Object.keys(data['Time Series (Daily)']).reverse();
            const adjClosePrices = dates.map(date => parseFloat(data['Time Series (Daily)'][date]['5. adjusted close']));

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
    let stockUrl = `https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=${stockSymbol}&outputsize=full&apikey=${apiKey}`;
    let spyUrl = `https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=${spysymbol}&outputsize=full&apikey=${apiKey}`;

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
                    let stockReturn = stockData['Time Series (Daily)'][date]['5. adjusted close'] / stockData['Time Series (Daily)'][Object.keys(stockData['Time Series (Daily)'])[0]]['5. adjusted close'] - 1;
                    let SPYReturn = SPYData['Time Series (Daily)'][date]['5. adjusted close'] / SPYData['Time Series (Daily)'][Object.keys(SPYData['Time Series (Daily)'])[0]]['5. adjusted close'] - 1;
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
                title: `${stockSymbol} and SPY Cumulative Returns`,
                xaxis: {
                    title: 'Date'
                },
                yaxis: {
                    title: 'Relative Price'
                }
            };

            Plotly.newPlot('comparisonChart', data, layout);
        })
        .catch(error => {
            console.error('Error fetching data from Alpha Vantage:', error);
        });

}

function makeDailyChangePlot(stockSymbol, spysymbol) {
    let stockUrl = `https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=${stockSymbol}&outputsize=full&apikey=${apiKey}`;
    let spyUrl = `https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=${spysymbol}&outputsize=full&apikey=${apiKey}`;

    Promise.all([fetch(stockUrl).then(response => response.json()), fetch(spyUrl).then(response => response.json())])
        .then(([stockData, SPYData]) => {
            if (!stockData['Time Series (Daily)'] || !SPYData['Time Series (Daily)']) {
                console.error('Time Series (Daily) data is not available');
                return;
            }

            let dates = [];
            let stockChanges = [];
            let SPYChanges = [];

            let previousStockClose = null;
            let previousSPYClose = null;

            for (let date in stockData['Time Series (Daily)']) {
                if (date in SPYData['Time Series (Daily)']) {
                    let stockClose = parseFloat(stockData['Time Series (Daily)'][date]['5. adjusted close']);
                    let SPYClose = parseFloat(SPYData['Time Series (Daily)'][date]['5. adjusted close']);

                    if (previousStockClose !== null && previousSPYClose !== null) {
                        let stockChange = (stockClose - previousStockClose) / previousStockClose;
                        let SPYChange = (SPYClose - previousSPYClose) / previousSPYClose;

                        dates.push(date);
                        stockChanges.push(stockChange);
                        SPYChanges.push(SPYChange);
                    }

                    previousStockClose = stockClose;
                    previousSPYClose = SPYClose;
                }
            }

            let trace1 = {
                x: dates,
                y: stockChanges,
                mode: 'lines',
                name: stockSymbol
            };

            let trace2 = {
                x: dates,
                y: SPYChanges,
                mode: 'lines',
                name: 'SPY'
            };

            let data = [trace1, trace2];

            let layout = {
                title: `Daily Percent Change in Returns for ${stockSymbol} and SPY`,
                xaxis: {
                    title: 'Date'
                },
                yaxis: {
                    title: 'Percent Change'
                }
            };

            Plotly.newPlot('dailyChangeChart', data, layout);
        })
        .catch(error => {
            console.error('Error fetching data from Alpha Vantage:', error);
        });
}

function makeScatterPlot(stockSymbol, spysymbol) {
    let stockUrl = `https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=${stockSymbol}&outputsize=full&apikey=${apiKey}`;
    let spyUrl = `https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=${spysymbol}&outputsize=full&apikey=${apiKey}`;
    Promise.all([fetch(stockUrl).then(response => response.json()), fetch(spyUrl).then(response => response.json())])
        .then(([stockData, SPYData]) => {
            if (!stockData['Time Series (Daily)'] || !SPYData['Time Series (Daily)']) {
                console.error('Time Series (Daily) data is not available');
                return;
            }
            let dates = [];
            let stockReturns = [];
            let SPYReturns = [];
            let previousStockClose = null;
            let previousSPYClose = null;
            for (let date in stockData['Time Series (Daily)']) {
                if (date in SPYData['Time Series (Daily)']) {
                    let stockClose = parseFloat(stockData['Time Series (Daily)'][date]['5. adjusted close']);
                    let SPYClose = parseFloat(SPYData['Time Series (Daily)'][date]['5. adjusted close']);
                    if (previousStockClose !== null && previousSPYClose !== null) {
                        let stockReturn = (stockClose - previousStockClose) / previousStockClose;
                        let SPYReturn = (SPYClose - previousSPYClose) / previousSPYClose;
                        dates.push(date);
                        stockReturns.push(stockReturn);
                        SPYReturns.push(SPYReturn);
                    }
                    previousStockClose = stockClose;
                    previousSPYClose = SPYClose;
                }
            }
            let trace = {
                x: SPYReturns,
                y: stockReturns,
                mode: 'markers',
                type: 'scatter',
                name: 'Return'
            };
            let layout = {
                title: `Scatter Graph of ${stockSymbol} vs SPY Returns, with Regression Line`,
                xaxis: {
                    title: 'SPY Return'
                },
                yaxis: {
                    title: `${stockSymbol} Return`
                }
            };
            let data = [trace];
            Plotly.newPlot('scatterChart', data, layout);
            Plotly.addTraces('scatterChart', {
                x: SPYReturns,
                y: regressionLine(SPYReturns, stockReturns),
                mode: 'lines',
                name: 'Fit'
            });
        })
        .catch(error => {
            console.error('Error fetching data from Alpha Vantage:', error);
        });
}
