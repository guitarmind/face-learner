/*
Based on Web demo of OpenFace.
Author: Mark Peng (markpeng.ntu@gmail.com)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

navigator.getUserMedia = navigator.getUserMedia ||
    navigator.webkitGetUserMedia ||
    navigator.mozGetUserMedia ||
    navigator.msGetUserMedia;

window.URL = window.URL ||
    window.webkitURL ||
    window.msURL ||
    window.mozURL;

var vid = document.getElementById('video-box'),
    vidReady = false;
var socket, socketName;

function sendFrameLoop() {
    if (socket == null || socket.readyState != socket.OPEN || !vidReady) {
        return;
    }

    // capture snapshot image from video box
    var canvas = document.createElement('canvas');
    canvas.width = vid.width;
    canvas.height = vid.height;
    var cc = canvas.getContext('2d');
    cc.drawImage(vid, 0, 0, vid.width, vid.height);
    var dataURL = canvas.toDataURL('image/jpeg', 0.6);

    // send as message to websocket server
    var msg = {
        'type': 'FRAME',
        'dataURL': dataURL,
        'labeled': null
    };
    socket.send(JSON.stringify(msg));

    setTimeout(function() {requestAnimFrame(sendFrameLoop)}, 250);
}

function umSuccess(stream) {
    if (vid.mozCaptureStream) {
        vid.mozSrcObject = stream;
    } else {
        vid.src = (window.URL && window.URL.createObjectURL(stream)) ||
            stream;
    }
    vid.play();
    vidReady = true;
    sendFrameLoop();
}

function getDataURLFromRGB(rgb) {
    var rgbLen = rgb.length;

    var canvas = $('<canvas/>').width(96).height(96)[0];
    var ctx = canvas.getContext("2d");
    var imageData = ctx.createImageData(96, 96);
    var data = imageData.data;
    var dLen = data.length;
    var i = 0, t = 0;

    for (; i < dLen; i +=4) {
        data[i] = rgb[t+2];
        data[i+1] = rgb[t+1];
        data[i+2] = rgb[t];
        data[i+3] = 255;
        t += 3;
    }
    ctx.putImageData(imageData, 0, 0);

    return canvas.toDataURL("image/png");
}

function createSocket(address, name) {
    socket = new WebSocket(address);
    socketName = name;
    socket.binaryType = "arraybuffer";
    socket.onopen = function() {
        $("#server-status").html("Connected to " + name + " Websocket server");
    }
    socket.onmessage = function(e) {
        console.log(e);
        json = JSON.parse(e.data)
        if (json.type == "ANNOTATED") {
            console.log(json)
            $("#detected-faces").html(
                "<img src='" + json['content'] + "' width='400px'></img>"
            );
            $("#processing-time").html(
                "Processing time: <strong>" + json['processing_time'] + "</strong> ms"
            );
            
        } else {
            console.log("Unrecognized message type: " + json.type);
        }
    }
    socket.onerror = function(e) {
        console.log("Error creating WebSocket connection to " + address);
        console.log(e);
    }
    socket.onclose = function(e) {
        if (e.target == socket) {
            $("#server-status").html("Disconnected.");
        }
    }
}
