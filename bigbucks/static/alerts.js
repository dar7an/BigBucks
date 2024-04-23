window.onload = function () {
    const messages = JSON.parse(document.getElementById('flash-messages').textContent);
    if (messages.length) {
        messages.forEach(function (message) {
            alert(message);
        });
    }
};
