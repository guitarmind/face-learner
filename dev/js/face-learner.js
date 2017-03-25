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
// a list of detected people and face thumbnail until now
var people = {}, images = [];
var colors = palette('cb-Paired', 10);

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
        'dataURL': dataURL
    };
    socket.send(JSON.stringify(msg));

    setTimeout(function() {requestAnimFrame(sendFrameLoop)}, 450);
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

function labelPersonCallback(e, id, text) {
    // send as message to websocket server
    var msg = {
        'type': 'LABELED',
        'uuid': id,
        'name': text
    };
    socket.send(JSON.stringify(msg)); 
}

function createSocket(address, name) {
    socket = new WebSocket(address);
    socketName = name;
    socket.binaryType = "arraybuffer";
    socket.onopen = function() {
        $("#server-status").html("Connected to " + name + " Websocket server");

        // convert hex color to RGB
        rgbColors = colors.map(hexToRgb)
        // send as message to websocket server
        var msg = {
            'type': 'PALETTE',
            'colors': rgbColors,
            'colors_hex': colors
        };
        socket.send(JSON.stringify(msg));
    }
    socket.onmessage = function(e) {
        json = JSON.parse(e.data)
        if (json.type == "ANNOTATED") {
            var frameFaces = json['frame_faces']
            for (var i = 0; i < frameFaces.length; i++) {
                face = frameFaces[i]
                tbody = $("#face-table").find('tbody')
                // see if this person has been listed in the face table
                if (tbody.find('#' + face['uuid']).length == 0) {
                    var row = (
                        '<tr>' +
                        '<td>'+ (Object.keys(people).length + 1) +'</td>'+
                        '<td>' +
                          '<div class="color-box round-corner" style="background-color: #' +
                            face['color'] + ';"></div>' +
                        '</td>'+
                        '<td>'+
                          '<div class="form-group">' +
                            '<input type="text" class="form-control" id="' + face['uuid'] + '" ' +
                                'value="' + face['name'] +'">' +
                          '</div>' +
                        '</td>'+
                        '</tr>'
                    );
                    tbody.append(row);

                    // bind press enter callback
                    $('#' + face['uuid']).pressEnter(labelPersonCallback);

                    people[face['uuid']] = {
                        'name': face['name'],
                        'color': face['color']
                    }
                }
            }

            $("#detected-faces").html(
                "<img src='" + json['content'] + "'></img>"
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
