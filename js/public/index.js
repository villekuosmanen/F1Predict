document.addEventListener("DOMContentLoaded", function(event) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'circuitName.txt');
    xhr.onload = function() {
        if (xhr.status === 200) {
            document.getElementById("gpNameHeader").innerHTML = xhr.responseText +
                ' GP - Qualifying predictions';
        }
        else {
            alert('Request failed.  Returned status of ' + xhr.status);
        }
    };
    xhr.send();
});