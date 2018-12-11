var buttonRecord = document.getElementById("record");

buttonRecord.onclick = function() {


    
    // XMLHttpRequest
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            // alert(xhr.responseText);
        }
    }
    xhr.open("POST", "/record_status");
    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xhr.send(JSON.stringify({ status: "true" }));
    var downloadLink = document.getElementById("download");
    downloadLink.text = "Download Image";
    downloadLink.href = "static/buf.jpeg";
};

